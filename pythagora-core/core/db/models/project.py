import re
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Union
from unicodedata import normalize
from uuid import UUID, uuid4

from sqlalchemy import Row, and_, delete, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, selectinload
from sqlalchemy.sql import func

from core.db.models import Base, File

if TYPE_CHECKING:
    from core.db.models import Branch


class Project(Base):
    __tablename__ = "projects"

    # ID and parent FKs
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Attributes
    name: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    folder_name: Mapped[str] = mapped_column(
        default=lambda context: Project.get_folder_from_project_name(context.get_current_parameters()["name"])
    )
    project_type: Mapped[str] = mapped_column(default="node")

    # Relationships
    branches: Mapped[list["Branch"]] = relationship(back_populates="project", cascade="all", lazy="raise")

    @staticmethod
    async def get_by_id(session: "AsyncSession", project_id: Union[str, UUID]) -> Optional["Project"]:
        """
        Get a project by ID.

        :param session: The SQLAlchemy session.
        :param project_id: The project ID (as str or UUID value).
        :return: The Project object if found, None otherwise.
        """
        if not isinstance(project_id, UUID):
            project_id = UUID(project_id)

        result = await session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def rename(session: "AsyncSession", id: UUID, name: str, dir_name: str) -> Optional["Project"]:
        """
        Rename a project and update its folder name.

        :param session: The SQLAlchemy session.
        :param id: The project ID.
        :param name: The new project name.
        :param dir_name: The new folder name for the project.
        :return: The updated Project object if found, None otherwise.
        """
        # Get the project by ID
        query = select(Project).where(Project.id == id)
        result = await session.execute(query)
        project = result.scalar_one_or_none()

        if project is None:
            return None

        # Update project name and dir name
        project.name = name
        project.folder_name = dir_name

        return project

    async def get_branch(self, name: Optional[str] = None) -> Optional["Branch"]:
        """
        Get a project branch by name.

        :param session: The SQLAlchemy session.
        :param branch_name: The name of the branch (default "main").
        :return: The Branch object if found, None otherwise.
        """
        from core.db.models import Branch

        session = inspect(self).async_session
        if session is None:
            raise ValueError("Project instance not associated with a DB session.")

        if name is None:
            name = Branch.DEFAULT

        result = await session.execute(select(Branch).where(Branch.project_id == self.id, Branch.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_file_for_project(session: AsyncSession, project_state_id: UUID, path: str) -> Optional["File"]:
        file_result = await session.execute(
            select(File).where(File.project_state_id == project_state_id, File.path == path)
        )
        return file_result.scalar_one_or_none()

    @staticmethod
    async def get_branches_for_project_id(session: AsyncSession, project_id: UUID) -> list["Branch"]:
        from core.db.models import Branch

        branch_result = await session.execute(select(Branch).where(Branch.project_id == project_id))
        return branch_result.scalars().all()

    @staticmethod
    async def get_all_projects(session: "AsyncSession") -> list[Row]:
        query = select(Project.id, Project.name, Project.created_at, Project.folder_name).order_by(Project.name)

        result = await session.execute(query)
        return result.fetchall()

    @staticmethod
    async def get_all_projects_with_branches_states(session: "AsyncSession") -> list["Project"]:
        """
        Get all projects.

        This assumes the projects have at least one branch and one state.

        :param session: The SQLAlchemy session.
        :return: List of Project objects.
        """
        from core.db.models import Branch, ProjectState

        latest_state_query = (
            select(ProjectState.branch_id, func.max(ProjectState.step_index).label("max_index"))
            .group_by(ProjectState.branch_id)
            .subquery()
        )

        query = (
            select(Project, Branch, ProjectState)
            .join(Branch, Project.branches)
            .join(ProjectState, Branch.states)
            .join(
                latest_state_query,
                and_(
                    ProjectState.branch_id == latest_state_query.columns.branch_id,
                    ProjectState.step_index == latest_state_query.columns.max_index,
                ),
            )
            .options(selectinload(Project.branches), selectinload(Branch.states))
            .order_by(Project.name, Branch.name)
        )

        results = await session.execute(query)
        return results.scalars().all()

    @staticmethod
    def get_folder_from_project_name(name: str):
        """
        Get the folder name from the project name.

        :param name: Project name.
        :return: Folder name.
        """
        # replace unicode with accents with base characters (eg "šašavi" → "sasavi")
        name = normalize("NFKD", name).encode("ascii", "ignore").decode("utf-8")

        # replace spaces/interpunction with a single dash
        return re.sub(r"[^a-zA-Z0-9]+", "-", name).lower().strip("-")

    @staticmethod
    async def delete_by_id(session: "AsyncSession", project_id: UUID) -> int:
        """
        Delete a project by ID.

        :param session: The SQLAlchemy session.
        :param project_id: The project ID
        :return: Number of rows deleted.
        """

        result = await session.execute(delete(Project).where(Project.id == project_id))
        return result.rowcount
