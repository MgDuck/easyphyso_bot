#!/usr/bin/env python3
"""
Синхронная версия PhySO Service для демонстрации (без Celery)
"""
import logging
from fastapi import FastAPI, HTTPException, Header, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from core.entities.prediction import Prediction as PredictionEntity
from config.database import get_repositories
from infra.physo.physo_service import PhySoService

app = FastAPI(
    debug=True,
    title="PhySO API (Demo)",
    version="1.0.0",
    description="PhySO Symbolic Regression Service - Demo Version",
)

# Получаем репозитории
repos = get_repositories()
user_repo = repos['user_repo']
model_repo = repos['model_repo']
prediction_repo = repos['prediction_repo']
transaction_repo = repos['transaction_repo']

# PhySO сервис
physo_service = PhySoService()

class PredictionCreateRequest(BaseModel):
    """Request model for creating a new PhySO prediction."""
    user_id: int = Field(..., description="The internal ID of the user requesting the prediction.")
    input_data: str = Field(..., description="CSV data for symbolic regression.")
    y_name: str = Field("y", description="Target variable name.")
    x_names: Optional[List[str]] = Field(None, description="Input variable names.")
    epochs: int = Field(50, description="Number of training epochs.")
    op_names: Optional[List[str]] = Field(None, description="Operations to use.")
    free_consts_names: Optional[List[str]] = Field(None, description="Free constants.")
    run_config: str = Field("config0", description="PhySO configuration.")
    stop_reward: float = Field(0.999, description="Stopping criterion (R²).")
    parallel_mode: bool = Field(False, description="Parallel execution mode.")

class PredictionResponse(PredictionEntity):
    """Response model for prediction details."""
    pareto_csv: Optional[Dict[str, Any]] = None

@app.get("/")
def health():
    return "ok"

@app.get("/version")
def version():
    return app.version

@app.post("/api/v1/predictions/", response_model=PredictionResponse, status_code=200)
async def create_prediction_sync(
    request: PredictionCreateRequest,
    x_api_key: str = Header(..., alias="X-API-KEY"),
) -> PredictionResponse:
    """
    Создает и сразу обрабатывает предсказание PhySO (синхронно для демо)
    """
    logging.info("API: Получен запрос на предсказание")
    
    # Проверяем API ключ и пользователя
    api_user = user_repo.get_by_api_key(x_api_key)
    if not api_user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if api_user.id != request.user_id:
        raise HTTPException(status_code=403, detail="API key does not match user")
    
    # Проверяем баланс
    if api_user.balance <= 0:
        raise HTTPException(status_code=402, detail="Insufficient balance")
    
    # Получаем активную модель
    model = model_repo.get_active_model()
    if not model:
        raise HTTPException(status_code=503, detail="No active model available")
    
    # Рассчитываем стоимость
    total_cost = physo_service.calculate_cost(model.base_price, model.epoch_price, request.epochs)
    
    if api_user.balance < total_cost:
        raise HTTPException(
            status_code=402, 
            detail=f"Insufficient balance. Required: ${total_cost:.4f}, Available: ${api_user.balance:.4f}"
        )
    
    # Создаем запись предсказания
    pred = PredictionEntity(
        user_id=api_user.id,
        model_id=model.id,
        input_data=request.input_data,
        y_name=request.y_name,
        x_names=request.x_names,
        epochs=request.epochs,
        op_names=request.op_names,
        free_consts_names=request.free_consts_names,
        run_config=request.run_config,
        stop_reward=request.stop_reward,
        parallel_mode=request.parallel_mode,
        status="processing",
    )
    pred = prediction_repo.add(pred)
    
    try:
        # Обрабатываем PhySO
        start_time = datetime.now()
        
        physo_data = {
            'input_data': request.input_data,
            'y_name': request.y_name,
            'x_names': request.x_names,
            'epochs': request.epochs,
            'op_names': request.op_names,
            'free_consts_names': request.free_consts_names,
            'run_config': request.run_config,
            'stop_reward': request.stop_reward,
            'parallel_mode': request.parallel_mode
        }
        
        physo_result = await physo_service.train(physo_data)
        process_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Обновляем результаты
        pred.best_formula = physo_result.get('best_formula')
        pred.best_r2 = physo_result.get('best_r2')
        pred.pareto_count = physo_result.get('pareto_count', 0)
        pred.metadata = physo_result.get('metadata', {})
        pred.total_cost = total_cost
        pred.status = 'completed' if physo_result['success'] else 'failed'
        pred.process_time = process_time_ms
        pred.completed_at = datetime.now()
        
        prediction_repo.update(pred)
        
        # Обновляем баланс пользователя
        new_balance = api_user.balance - total_cost
        user_repo.update_balance(api_user.id, new_balance)
        
        # Создаем транзакцию
        from core.entities.transaction import Transaction
        transaction = Transaction(
            user_id=api_user.id,
            amount=-total_cost,
            description=f"PhySO prediction {pred.uuid} ({request.epochs} epochs)",
            prediction_id=pred.id
        )
        transaction_repo.add(transaction)
        
        logging.info(f"✅ Предсказание завершено: {pred.uuid}")
        return PredictionResponse(
            **pred.dict(),
            pareto_csv=physo_result.get('pareto_csv')
        )
        
    except Exception as e:
        # Обновляем статус на failed
        pred.status = 'failed'
        pred.completed_at = datetime.now()
        pred.best_formula = f"Error: {str(e)}"
        prediction_repo.update(pred)
        
        logging.error(f"❌ Ошибка предсказания: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/api/v1/predictions/upload/", response_model=PredictionResponse, status_code=200)
async def create_prediction_with_file_sync(
    file: UploadFile = File(..., description="CSV file with data"),
    user_id: int = Form(..., description="User ID"),
    y_name: str = Form("y", description="Target variable name"),
    x_names: Optional[str] = Form(None, description="Input variable names (JSON list)"),
    epochs: int = Form(50, description="Number of training epochs"),
    op_names: Optional[str] = Form(None, description="Operations to use (JSON list)"),
    free_consts_names: Optional[str] = Form(None, description="Free constants (JSON list)"),
    run_config: str = Form("config0", description="PhySO configuration"),
    stop_reward: float = Form(0.999, description="Stopping criterion (R²)"),
    parallel_mode: bool = Form(False, description="Parallel execution mode"),
    x_api_key: str = Header(..., alias="X-API-KEY"),
) -> PredictionResponse:
    """
    Создает предсказание с загрузкой файла
    """
    # Проверяем тип файла
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Читаем файл
    try:
        contents = await file.read()
        input_data = contents.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Парсим JSON параметры
    try:
        x_names_list = json.loads(x_names) if x_names else None
    except:
        x_names_list = None
        
    try:
        op_names_list = json.loads(op_names) if op_names else None
    except:
        op_names_list = None
        
    try:
        free_consts_list = json.loads(free_consts_names) if free_consts_names else None
    except:
        free_consts_list = None
    
    # Создаем запрос
    request = PredictionCreateRequest(
        user_id=user_id,
        input_data=input_data,
        y_name=y_name,
        x_names=x_names_list,
        epochs=epochs,
        op_names=op_names_list,
        free_consts_names=free_consts_list,
        run_config=run_config,
        stop_reward=stop_reward,
        parallel_mode=parallel_mode
    )
    
    return await create_prediction_sync(request, x_api_key)

@app.get("/api/v1/predictions/{uuid}", response_model=PredictionResponse)
async def get_prediction_status(uuid: str):
    """Получить статус предсказания по UUID"""
    prediction = prediction_repo.get_by_uuid(uuid)
    if prediction:
        return PredictionResponse(**prediction.dict())
    else:
        raise HTTPException(status_code=404, detail=f"Prediction with UUID {uuid} not found")

@app.get("/api/v1/predictions/user/{user_id}", response_model=List[PredictionResponse])
async def get_user_predictions(
    user_id: int, 
    x_api_key: str = Header(..., alias="X-API-KEY")
):
    """Получить все предсказания пользователя"""
    # Проверяем API ключ
    api_user = user_repo.get_by_api_key(x_api_key)
    if not api_user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if api_user.id != user_id:
        raise HTTPException(status_code=403, detail="API key does not grant access to this user's predictions")
    
    predictions = prediction_repo.list_by_user(user_id)
    return [PredictionResponse(**prediction.dict()) for prediction in predictions]

@app.get("/api/v1/users/{user_id}/balance")
async def get_user_balance(
    user_id: int,
    x_api_key: str = Header(..., alias="X-API-KEY")
):
    """Получить баланс пользователя"""
    api_user = user_repo.get_by_api_key(x_api_key)
    if not api_user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if api_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"balance": api_user.balance}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=53251)
