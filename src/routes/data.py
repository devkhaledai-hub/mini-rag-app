from fastapi import FastAPI, APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
import os
from helpers.config import get_settings, Settings
from controllers import DataController, ProjectController, ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemas.data import ProcessRequest  # Import all schemas from the schemas package
from models.ProjectModel import ProjectModel
from models.db_schemas import DataChunk, Asset
from models.ChunkModel import ChunkModel
from models.AssetModel import AssetModel
from models.enums.AssetTypeEnum import AssetTypeEnum
from controllers import NLPController


logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(prefix="/api/v1/data", tags=["api_v1", "data"])


@data_router.post("/upload/{project_id}")
async def upload_data(
    request: Request,
    project_id: int,
    file: UploadFile,
    app_settings: Settings = Depends(get_settings),
):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create_one(project_id=project_id)

    # validate the file properties
    data_controller = DataController()
    is_valid, result_signal = data_controller.validate_uploaded_file(file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"signal": result_signal}
        )
    # get the project path
    project_dir_path = ProjectController().get_project_path(project_id)

    # save the file to the project directory
    file_path, file_id = data_controller.generate_unique_filepath(
        original_filename=file.filename, project_id=project_id
    )

    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(
                app_settings.FILE_DEFAULT_CHUNK_SIZE
            ):  # Read the file in chunks
                await f.write(chunk)

    except Exception as e:
        logger.error(f"Error occurred while uploading file: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": ResponseSignal.FILE_UPLOAD_FAILURE.value},
        )
    # store the assets in the db 
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    asset_resource = Asset(
        
        asset_project_id=project.project_id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name=file_id,
        asset_size=os.path.getsize(file_path)
    )
    asset_record = await asset_model.create_asset(asset=asset_resource)

    return JSONResponse(
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value, 
            "file_id":str(asset_record.asset_id),
            }
    )


@data_router.post("/process/{project_id}")
async def process_endpoint(
    request: Request, project_id: int, process_request: ProcessRequest
):

    chunk_size = process_request.chunk_size
    overlap = process_request.overlap
    do_reset = process_request.do_reset

    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
        )
    project = await project_model.get_project_or_create_one(
        project_id=project_id
        )
    
    nlp_controller = NLPController(
        vectordb_client=request.app.vectordb_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser
        )

    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    project_files_ids={}

    if process_request.file_id:
        if process_request.file_id.isdigit():
            asset_record = await asset_model.get_asset_record_by_id(
                asset_project_id=project.project_id,
                asset_id=int(process_request.file_id)
            )
        else:
            asset_record = await asset_model.get_asset_record(
                asset_project_id=project.project_id,
                asset_name=process_request.file_id
            )

        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.FILE_ID_ERROR.value,
                    "message": f"No file found with the provided file_id: {process_request.file_id} for the project.",
                },
            )

        project_files_ids = {
            asset_record.asset_uuid: asset_record.asset_name
        }
    else:
        project_files = await asset_model.get_all_project_assets(
            asset_project_id=project.project_id,
            asset_type=AssetTypeEnum.FILE.value
        )
        project_files_ids = {
            record.asset_uuid: record.asset_name
            for record in project_files
        }


    if len(project_files_ids) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.NO_FILES_ERROR.value,
                "message": "No files found for the project to process.",
            },
        )

    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
        )

    if do_reset == 1:
        # Delete associated vector db collection
        collection_name = nlp_controller.create_collection_name(project_id=project.project_id)
        
        # delete associated chunks in the db
        _ = await request.app.vectordb_client.delete_collection(collection_name=collection_name)

        _ = await chunk_model.delete_chunks_by_project_id(
            project_id=project.project_uuid
            )

    process_controller = ProcessController(project_id=project_id)
    no_records = 0
    no_files=0

    for asset_uuid, file_id in project_files_ids.items():
        file_content, result_message  = process_controller.get_file_content(file_id=file_id)
        
        if file_content is None:
            logger.error(f"Error occurred while loading file content for file_id: {file_id}")
            continue
        
        file_chunks, result_message = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignal.PROCESSING_FAILURE.value,
                    "message": result_message,
                },
            )
        file_chunks_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i + 1,
                chunk_project_id=project.project_uuid,
                chunk_asset_id=asset_uuid
            )
            for i, chunk in enumerate(file_chunks)
        ]

        no_records += await chunk_model.insert_many_chunks(chunks=file_chunks_records)
        no_files+=1

    if no_files == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.PROCESSING_FAILURE.value,
                "message": "No files could be loaded for processing.",
            },
        )
        
    return JSONResponse(
        content={
            "signal": ResponseSignal.PROCESSING_SUCCESS.value,
            "inserted_chunks": no_records,
            "processed_files": no_files,
        }
    )
