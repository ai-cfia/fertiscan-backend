from app.models.items import ItemCreate, ItemDB

fake_items_db: dict[str, ItemDB] = {}


def create(item: ItemCreate):
    item_db = ItemDB.model_validate(item.model_dump())
    fake_items_db[str(item_db.id)] = item_db
    return item_db


def read(id: str):
    return fake_items_db[id]


def read_all():
    return list(fake_items_db.values())
