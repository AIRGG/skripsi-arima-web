from routes.imports import *
from utils.arima import ArimaModule
from utils.koneksi import Connection

import pandas as pd

arima = ArimaModule()

routes_arima = APIRouter()
# schema_device = sqlalchemy_to_pydantic(TblDevice)
class response_predict_device(BaseModel):
    id_device:Optional[str]=''
    name_device:Optional[str]=''
    id_customer:Optional[str]=''
    name_customer:Optional[str]=''
    key_sensor:Optional[str]=''
    name_sensor:Optional[str]=''

class response_login(BaseModel):
    token: str = ''
    refreshToken: str = ''

class request_predict(BaseModel):
    start_tarik_data: str = '2023-08-01'
    end_tarik_data: str = '2023-12-15'

    start_train_data: str = '2023-08-01'
    end_train_data: str = '2023-12-15'

    start_date: str = '2023-12-16'
    end_date: str = '2023-12-31'

    device_id: str = '1ee01383af6c0308c68d371b81349fd'
    sensor_key: str = 'usage1'

class response_predict(BaseModel):
    graph_month: List[Union[float, int]] = []
    graph_month_label: List[str] = []
    graph_day: List[Union[float, int]] = []
    graph_day_label: List[str] = []
    identity: Optional[response_predict_device] = None
    # device: any
    # token: str = ''

@routes_arima.post("/arima/predict", response_model=response_predict)
async def process_predict(
    request: Request,
    response: Response,
    payload: request_predict
):
    http: httpx = request.state.httpx
    conn: Connection = request.state.conn
    print(payload, 'payload')

    # start_date_str_tarik_data: str = '2023-08-01'
    # end_date_str_tarik_data: str = '2023-11-15'

    # start_date_str_train: str = '2023-08-01'
    # end_date_str_train: str = '2023-11-15'

    start_date_str_tarik_data: str = payload.start_tarik_data
    end_date_str_tarik_data: str = payload.end_tarik_data

    start_date_str_train: str = payload.start_train_data
    end_date_str_train: str = payload.end_train_data

    start_date_str_test: str = payload.start_date
    end_date_str_test: str = payload.end_date

    device_id = payload.device_id
    sensor_key = payload.sensor_key

    model_pk_path = os.path.join(os.getcwd(), 'arima_models', f"arima_{device_id}_{sensor_key}_{start_date_str_train}_{end_date_str_train}.pkl")
    df_merge_pk_path = os.path.join(os.getcwd(), 'arima_models', f"df_merge_{device_id}_{sensor_key}_{start_date_str_train}_{end_date_str_train}.pkl")

    # simple cache for fast execute if exists
    if pathlib.Path(model_pk_path).exists() and pathlib.Path(df_merge_pk_path).exists():
        print('#=================#')
        print('#-- using cache --#')
        print('#=================#')
        model = joblib.load(model_pk_path)
        df_merge = joblib.load(df_merge_pk_path)
    else:
        print('#==================#')
        print('#-- create model --#')
        print('#==================#')
        # print(pd.to_datetime(f'{start_date_str_train}'))
        # print(pd.to_datetime(f'{end_date_str_train} 23:59:59'))
        # return {}
        df_history = await arima.get_data(conn, device_id, sensor_key, start_date_str_tarik_data, end_date_str_tarik_data)

        # data kosong
        if len(df_history.index) == 0:
            return {
                "graph_month": [],
                "graph_month_label": [],
                "graph_day": [],
                "identity": {
                    "id_device": "",
                    "name_device": "",
                    "id_customer": "",
                    "name_customer": "",
                    "key_sensor": "",
                    "name_sensor": "",
                }
                }
        # print(df_history, 'df_history')
        # return {}

        df_history.sort_values(by=["ts"], inplace=True)
        df_history['timestamp'] = df_history['ts'].to_list()
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp'], unit="ms")
        # print(df_history.columns)
        df_history.set_index('timestamp', inplace=True)
        # df_history.index = df_history.index.tz_localize(pytz.utc)
        df_history = df_history.loc[pd.to_datetime(start_date_str_train):pd.to_datetime(f'{end_date_str_train} 23:59:59.999999')]
        # print(df_history.index)
        print(df_history, 'df_history')
        print(df_history[['ts']], 'df_history')
        
        model, df_merge = await arima.create_model(df_history, device_id, sensor_key, start_date_str_train, end_date_str_train)
    # .replace(tzinfo=pytz.utc).astimezone(timezone)
    
    # model = joblib.load(model_pk)
    df_result = await arima.predict(model, start_date_str_test, end_date_str_test)
    res = await arima.wrapping_up(df_merge, df_result)
    res['identity']['key_sensor'] = sensor_key
    res['identity']['name_sensor'] = await arima.get_sensor_name(conn, sensor_key)
    print(res, 'res')
    return res

@routes_arima.post("/arima/get-data")
async def process_get_data(
    request: Request,
    response: Response
):
    http: httpx = request.state.httpx

    form = await request.form()
    print(form)
    return []