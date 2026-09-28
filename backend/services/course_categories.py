"""Category suggestions and create-on-course-save, without a management flow."""
import uuid
from fastapi import HTTPException
from sqlalchemy import select, text
from models.models import Category, Course


def category_name(value):
    if not isinstance(value, str):
        raise HTTPException(400, "Category must be a name")
    name = " ".join(value.split())
    if not name or len(name) > 100:
        raise HTTPException(400, "Category must contain 1–100 characters")
    return name


async def category_options(db):
    """Include legacy names already assigned to courses; never write on a GET."""
    rows = (await db.execute(select(Category).order_by(Category.created_at, Category.id))).scalars().all()
    options = {}
    for row in rows:
        name = " ".join(row.name.split())
        if name:
            options.setdefault(name.lower(), {"name": name, "category_id": row.category_id})
    existing = (await db.execute(select(Course.category).distinct())).scalars().all()
    for value in existing:
        name = " ".join((value or "").split())
        if name:
            options.setdefault(name.lower(), {"name": name, "category_id": None})
    return sorted(options.values(), key=lambda option: option["name"].lower())


async def resolve_course_category(db, value):
    """Reuse names ignoring case/spacing. Caller owns the course transaction."""
    name = category_name(value)
    # Two admins saving the same new name must not create duplicate categories.
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key)::bigint)"),
                     {"key": f"course-category:{name.lower()}"})
    existing = next((item for item in await category_options(db)
                     if item["name"].lower() == name.lower()), None)
    if existing:
        name = existing["name"]
        if existing["category_id"]:
            return name
    db.add(Category(category_id=f"cat_{uuid.uuid4().hex[:16]}", name=name))
    await db.flush()
    return name