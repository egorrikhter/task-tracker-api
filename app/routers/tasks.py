from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import delete, func, select

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, Tag, Task, User
from app.schemas import (
    PaginatedResponse,
    TagName,
    TaskCreate,
    TaskRead,
    TaskStatus,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(
    task_data: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    project = (
        await db.execute(
            select(Project).where(
                Project.id == task_data.project_id, Project.owner_id == current_user.id
            )
        )
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )

    if task_data.assignee_id is not None and task_data.assignee_id != current_user.id:
        raise HTTPException(
            status_code=400, detail="You can only assign tasks to yourself."
        )

    task = Task(
        title=task_data.title,
        status=task_data.status,
        assignee_id=task_data.assignee_id,
        project_id=task_data.project_id,
        creator_id=current_user.id,
    )

    db.add(task)
    try:
        await db.commit()
        await db.refresh(task)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="The task name within the project must be unique."
        )
    return task


@router.get("", response_model=PaginatedResponse[TaskRead])
async def get_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, ge=1, le=100),
    project_id: UUID | None = None,
    offset: int = Query(0, ge=0),
    status: TaskStatus | None = None,
    tag: TagName | None = None,
    order: str = Query("desc", pattern="^(asc|desc)$"),
):
    query = (
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(Project.owner_id == current_user.id)
    )

    if project_id is not None:
        query = query.where(Task.project_id == project_id)

    if status is not None:
        query = query.where(Task.status == status)

    if tag is not None:
        query = query.where(Task.tags.any(Tag.name == tag))

    count_query = select(func.count()).select_from(query.subquery())

    order_by_clause = (
        Task.created_at.desc() if order == "desc" else Task.created_at.asc()
    )

    query = (
        query.options(selectinload(Task.tags))
        .limit(limit)
        .offset(offset)
        .order_by(order_by_clause)
    )

    result = await db.execute(query)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    tasks = result.scalars().all()

    return {
        "items": tasks,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_id: UUID,
):
    query = (
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(Project.owner_id == current_user.id, Task.id == task_id)
    ).options(selectinload(Task.tags))

    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def patch_task(
    task_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    update_data: TaskUpdate,
):
    task = await db.scalar(
        select(Task)
        .join(Project, Project.id == Task.project_id)
        .where(Project.owner_id == current_user.id, Task.id == task_id)
        .options(selectinload(Task.tags))
    )
    if task is None:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )

    assignee_id = update_data.assignee_id

    if assignee_id is not None and assignee_id != current_user.id:
        raise HTTPException(
            status_code=400, detail="The UUID value does not meet the requirements."
        )

    update_data_dict = update_data.model_dump(exclude_unset=True)

    if not update_data_dict:
        return task

    if "tags" in update_data_dict:
        incoming_tags = update_data_dict.pop("tags")

        if not incoming_tags:
            task.tags = []

        else:
            result = await db.scalars(select(Tag).where(Tag.name.in_(incoming_tags)))
            existing_tags = result.all()
            existing_tags_set = {tag.name for tag in existing_tags}
            diff_tags = set(incoming_tags) - existing_tags_set
            new_tags = [Tag(name=name) for name in diff_tags]
            task.tags = new_tags + list(existing_tags)

    for key, value in update_data_dict.items():
        setattr(task, key, value)

    try:
        await db.commit()
        await db.refresh(task, attribute_names=["updated_at"])
    except IntegrityError as e:
        await db.rollback()

        cause = getattr(e.orig, "__cause__", e.orig)
        if isinstance(cause, asyncpg.UniqueViolationError):
            constraint = getattr(cause, "constraint_name", None)
            if constraint == "tags_name_key":
                raise HTTPException(
                    status_code=409,
                    detail="A tag with this name already exists or is being created concurrently. Please retry.",
                )
            elif constraint == "uq_title_and_project":
                raise HTTPException(
                    status_code=409,
                    detail="The task name must be unique within the project.",
                )
        raise

    return task


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    task_id: UUID,
):

    allowed_projects_subquery = select(Project.id).where(
        Project.owner_id == current_user.id
    )

    query = (
        delete(Task)
        .where(Task.id == task_id, Task.project_id.in_(allowed_projects_subquery))
        .returning(Task.id)
    )

    result = await db.scalar(query)

    if result is None:
        raise HTTPException(
            status_code=404, detail="The requested resource could not be found."
        )

    await db.commit()
