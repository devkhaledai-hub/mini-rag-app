from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from sqlalchemy.future import select
from sqlalchemy import func

class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.db_client = self.db_client


    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client=db_client)
        return instance



    async def create_project(self, project: Project):
        async with self.db_client() as session:
            session.add(project)
            await session.commit()
            await session.refresh(project)
        
        return project

        # result = await self.collection.insert_one(project.dict(by_alias=True, exclude_unset=True))
        # project.project_id = result.inserted_id
        # return project
    

    async def get_project_or_create_one(self, project_id: str):
        async with self.db_client() as session:
            query = select(Project).where(Project.project_id == project_id)
            result = await session.execute(query)
            project = result.scalar_one_or_none()

            if project is None:
                project = Project(project_id=project_id)
                session.add(project)
                await session.commit()
                await session.refresh(project)

            return project


        # record = await self.collection.find_one(
        #     {
        #     "project_id": project_id
        #     }
        #     )
        # if record is None:
        #     project = Project(project_id=project_id)
        #     project = await self.create_project(project=project)
        #     return project
        
        # return Project(**record)
    

    async def get_all_projects(self, page: int = 1, page_size: int = 10):

        async with self.db_client() as session:
            async with session.begin():


                total_documents= await session.execute(
                    
                    select(
                        func.count(Project.project_id) # pylint: disable=not-callable
                        )
                    )
                total_documents = total_documents.scalar_one()

                total_pages = total_documents // page_size
                if total_documents % page_size > 0:
                    total_pages += 1

                query = select(Project).offset((page-1)*page_size).limit(page_size)
                result = await session.execute(query)
                projects = result.scalars().all()
                return projects, total_pages


        # # count the total number of records in the collection
        # total_documents = await self.collection.count_documents({})
        
        # # calculate number of pages
        # total_pages = total_documents // page_size
        # if total_documents % page_size > 0:
        #     total_pages += 1

        # self.collection.find({}).skip((page - 1) * page_size).limit(page_size)

        # cursor = self.collection.find({}).skip((page - 1) * page_size).limit(page_size)
        # projects = []
        # async for record in cursor:
        #     projects.append(Project(**record))

        # return projects, total_pages
    
