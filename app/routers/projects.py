from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, User
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = Project(title=project_data.title, owner_id=current_user.id)
    db.add(project)

    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def get_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Project).where(Project.owner_id == current_user.id)
    )
    projects = result.scalars().all()
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project_by_id(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = (
        await db.execute(
            select(Project).where(
                Project.id == project_id, Project.owner_id == current_user.id
            )
        )
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    update_data: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = (
        await db.execute(
            select(Project).where(
                Project.id == project_id, Project.owner_id == current_user.id
            )
        )
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        return project

    for key, value in update_dict.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = (
        await db.execute(
            select(Project).where(
                Project.id == project_id, Project.owner_id == current_user.id
            )
        )
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )

    await db.delete(project)
    await db.commit()
