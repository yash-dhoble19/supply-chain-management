from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import database
import models
import schemas.manufacturing
from services.manufacturing_service import (
    get_all_manufacturing_goods,
    get_manufacturing_goods_by_id,
    create_manufacturing_goods,
    update_manufacturing_goods,
    get_completed_manufacturing_goods,
)

router = APIRouter(prefix="/api/manufacturing", tags=["Manufacturing"])


@router.get("/", response_model=List[schemas.manufacturing.ManufacturingGoods])
def list_manufacturing_goods(db: Session = Depends(database.get_db)):
    return get_all_manufacturing_goods(db)


@router.post("/", response_model=schemas.manufacturing.ManufacturingGoods)
def create_manufacturing_task(
    goods: schemas.manufacturing.ManufacturingGoodsCreate,
    db: Session = Depends(database.get_db)
):
    # Check if SKU already exists
    existing = db.query(models.ManufacturingGoods).filter(models.ManufacturingGoods.sku == goods.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    return create_manufacturing_goods(db, goods)


@router.get("/completed", response_model=List[schemas.manufacturing.ManufacturingGoods])
def list_completed_manufacturing_goods(db: Session = Depends(database.get_db)):
    return get_completed_manufacturing_goods(db)


@router.get("/{goods_id}", response_model=schemas.manufacturing.ManufacturingGoods)
def get_manufacturing_goods(goods_id: int, db: Session = Depends(database.get_db)):
    goods = get_manufacturing_goods_by_id(db, goods_id)
    if not goods:
        raise HTTPException(status_code=404, detail="Manufacturing goods not found")
    return goods


@router.patch("/{goods_id}", response_model=schemas.manufacturing.ManufacturingGoods)
def update_manufacturing_task(
    goods_id: int,
    update_data: schemas.manufacturing.ManufacturingGoodsUpdate,
    db: Session = Depends(database.get_db)
):
    goods = update_manufacturing_goods(db, goods_id, update_data)
    if not goods:
        raise HTTPException(status_code=404, detail="Manufacturing goods not found")
    return goods


@router.put("/{goods_id}", response_model=schemas.manufacturing.ManufacturingGoods)
def replace_manufacturing_task(
    goods_id: int,
    update_data: schemas.manufacturing.ManufacturingGoodsUpdate,
    db: Session = Depends(database.get_db)
):
    # support PUT clients (e.g. frontend apiPut)
    goods = update_manufacturing_goods(db, goods_id, update_data)
    if not goods:
        raise HTTPException(status_code=404, detail="Manufacturing goods not found")
    return goods
# anything
