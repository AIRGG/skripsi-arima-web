from sqlalchemy import text
from statsmodels.tsa.stattools import adfuller

import pandas as pd
import numpy as np
import seaborn as sns
import pmdarima as pm
import matplotlib.pyplot as plt

import pytz
import datetime, asyncio, os, joblib, re

# from koneksi import Connection
from utils.koneksi import Connection

class ArimaModule():
    def __init__(self) -> None:
        pass

    async def get_data(self, conn, device_id, sensor_key, start_date='2023-08-01', end_date='2023-12-20'):
        timezone = pytz.timezone('GMT')
        ts_start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.utc).astimezone(timezone).timestamp()  * 1e3
        ts_end_date = datetime.datetime.strptime(f'{end_date} 23:59:59.999999', '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=pytz.utc).astimezone(timezone).timestamp()  * 1e3

        sql_device = text("SELECT * FROM device")
        print(sql_device, device_id, ts_start_date, ts_end_date)
        df_device = await conn.df_conniot(sql_device)
        df_device = df_device.rename(columns={'id': 'id_device'})
        sql_customer = text("SELECT * FROM customer")
        print(sql_customer)
        df_customer = await conn.df_conniot(sql_customer)
        df_customer = df_customer.rename(columns={'id': 'id_customer'})
        sql = text(f"SELECT * FROM ts_kv WHERE entity_id=:entity_id AND key=:key AND ts >= :ts_start AND ts <= :ts_end")
        sql = sql.bindparams(
            key=sensor_key,
            entity_id=device_id,
            ts_start=ts_start_date,
            ts_end=ts_end_date,
        )
        print(sql)
        df = await conn.df_conniot(sql)
        print(df)

        # df = pd.read_csv('df_1aug_31dec.csv')
        merged_df = pd.merge(df, pd.merge(df_device, df_customer[['id_customer', 'title']], left_on='customer_id', right_on='id_customer', how='left')[['id_device', 'id_customer', 'name', 'title']], left_on='entity_id', right_on='id_device', how='left')
        print(merged_df)
        merged_df = merged_df.rename(columns={'name': 'name_device', 'title': 'name_customer'})
        print(merged_df, 'merge last')
        return merged_df
    
    async def create_model(self, df_original_data, device_id='', sensor_key='', start_date_str_train='2023-08-01', end_date_str_train='2023-12-15'):
        # --------------
        # cleaning data
        # --------------
        df_original_data["value"] = (
            df_original_data["bool_v"]
            .fillna(df_original_data["str_v"])
            .fillna(df_original_data["long_v"])
            .fillna(df_original_data["dbl_v"])
        )
        df_original_data["value"] = pd.to_numeric(df_original_data["value"], errors="coerce")
        df_original_data.dropna(subset=["value"], inplace=True)
        # df_original_data['originalValue'] = df_original_data['value'].to_list()
        # df_original_data['originalKey'] = df_original_data['key'].to_list()
        # df_original_data['key'] = df_original_data['key'].str.replace('\d+', '', regex=True).to_list()
        df_original_data["timestamp"] = pd.to_datetime(df_original_data["ts"], unit="ms")
        df_original_data.sort_values(by=["ts"], inplace=True)
        df_original_data.drop([
            'bool_v',
            'str_v',
            'long_v',
            'dbl_v',
        ], axis=1, inplace=True)
        
        # usage = df_original_data[df_original_data["key"] == "usage"]
        usage = df_original_data.copy()
        usage.set_index('timestamp', inplace=True)
        usage['timestamp'] = usage.index

        # print(usage, 'usage')
        # usage.to_csv('df_usage.csv')

        # --------------
        # custom formula
        # --------------
        prevTelemetryValue = 0
        prevGraphValue = 0
        newGraphValue = 0
        arr_value = usage.value.to_list()
        # print(x, arr_value)
        print('prepare#2.1')
        for index in range(len(usage)):
            row = usage.iloc[index]
            # print(row)
            value = float(row.value)
            if index > 0:
                prevTelemetryValue = float(arr_value[index - 1])
                newTelemetryValue = value
                # kondisi 1
                if (prevGraphValue <= prevTelemetryValue):
                    if (newTelemetryValue > prevTelemetryValue):
                        newGraphValue = newTelemetryValue - prevTelemetryValue + prevGraphValue
                    else:
                        newGraphValue = prevGraphValue + newTelemetryValue
                else:
                    if(newTelemetryValue < prevTelemetryValue):
                        # b < a
                        newGraphValue = prevGraphValue + newTelemetryValue
                    else:
                        # b >= a
                        newGraphValue = newTelemetryValue - prevTelemetryValue + prevGraphValue
                prevGraphValue = newGraphValue
            else:
                newGraphValue = 0
                prevTelemetryValue = 0
                prevGraphValue = 0
            value = newGraphValue
            usage.at[row.timestamp, 'value'] = value
        # print(usage["value"])
        usage["value_back"] = usage['value']
        usage["value"] = usage["value"].diff()
        df_forecast=usage['value'].resample('d').sum()
        # df_forecast.to_pickle('df_forecast.pk')
        # usage.to_pickle('usage.pk')
        # return []
        # plt.plot(df_forecast)
        # plt.show()
        # print(df_resample, 'df_resample')
        # df_forecast = pd.read_pickle("df_forecast.pk")  
        # usage = pd.read_pickle("usage.pk")  

        # df_merge['timestamp'] = pd.to_datetime(df_resample.timestamp.values)
        # df_merge = df_resample.set_index('timestamp')
        # print(df_resample, 'df_resample')

        # --------------
        # cleaning data
        # --------------
        start_datetime_str_train = pd.to_datetime(start_date_str_train)
        end_datetime_str_train = pd.to_datetime(end_date_str_train)
        # train = df_forecast[(df_forecast.index.get_level_values(0) >= start_datetime_str_train) & (df_forecast.index.get_level_values(0) <= end_datetime_str_train)]
        train = df_forecast.loc[start_datetime_str_train:end_datetime_str_train]
        print(train)

        model = pm.auto_arima(train, m=1, d=1, seasonal=True, start_p=0, start_q=0, max_order=4, test='adf',error_action='ignore', suppress_warnings=True, stepwise=True, trace=True)
        model.fit(train)
        pk_model = os.path.join(os.getcwd(), 'arima_models', f"arima_{device_id}_{sensor_key}_{start_date_str_train}_{end_date_str_train}.pkl")
        pk_df = os.path.join(os.getcwd(), 'arima_models', f"df_merge_{device_id}_{sensor_key}_{start_date_str_train}_{end_date_str_train}.pkl")
        joblib.dump(model, pk_model, compress=3)
        # joblib.dump(model, df_forecast, compress=3)
        usage.to_pickle(pk_df)
        df_usage = usage['value'].resample('ME').sum()
        print(df_usage, 'df_usage')
        return model, usage
    
    async def predict(self, model, start_date_str_test, end_date_str_test):
        print(start_date_str_test, end_date_str_test)
        timezone = pytz.timezone('Asia/Jakarta')
        n_period = (datetime.datetime.strptime(end_date_str_test, '%Y-%m-%d') - datetime.datetime.strptime(start_date_str_test, '%Y-%m-%d')).days + 1
        # n_period = 15
        print(n_period, start_date_str_test, end_date_str_test)

        forecast_fix = model.predict(n_periods=n_period, return_conf_int=True)
        print(forecast_fix[0], 'forecast_fix')

        forecast_range = pd.date_range(start=start_date_str_test, periods=n_period, freq='d')
        print(forecast_range, 'forecast_range')
        forecast_fix_df = pd.DataFrame(forecast_fix[0], index=forecast_range,columns=['Prediction'])
        print(forecast_fix_df, 'forecast_fix_df')
        return forecast_fix_df
    
    async def get_sensor_name(self, conn, sensor_key=''):
        # sensor_key = 'usage1'
        sensor_key = re.sub('\d+', '', sensor_key)

        sql_telemetry = text("SELECT * FROM tbl_telemetry WHERE key_telemetry=:key_telemetry")
        sql_telemetry = sql_telemetry.bindparams(key_telemetry=sensor_key)
        df_telemetry: pd.DataFrame = await conn.df_connhelper(sql_telemetry)
        print(df_telemetry, df_telemetry.empty, 'df_telemetry')
        if df_telemetry.empty:
            return ''
        return df_telemetry.iloc[0].name_telemetry
    
    async def wrapping_up(self, df, predict, start_date_str_train='', end_date_str_train=''):
        # start_datetime_str_train = pd.to_datetime(start_date_str_train)
        # end_datetime_str_train = pd.to_datetime(f'{end_date_str_train} 23:59:59')
        # start_datetime_str_train = pd.to_datetime('2023-11-01')
        # end_datetime_str_train = pd.to_datetime('2023-11-16')
        
        # df = df[( >= start_datetime_str_train)]
        # print(start_datetime_str_train, type(start_datetime_str_train))
        # print(end_datetime_str_train, type(end_datetime_str_train))
        # print(df.columns)
        # print(df)
        df_forecast=df['value'].resample('d').sum()
        # df_tmp = df_forecast[(df_forecast.index.get_level_values(0) >= start_datetime_str_train) & (df_forecast.index.get_level_values(0) <= end_datetime_str_train)]
        # print(df_forecast.index.get_level_values(0) >= start_datetime_str_train)
        # df_forecast['timestamp'] = pd.to_datetime(df_forecast.timestamp.values)
        # df_forecast = df_forecast.set_index('timestamp')
        # print(df_forecast.index, type(df_forecast.index))
        # print(df_forecast)
        print(df_forecast, 'df_forecast')
        print(df_forecast.index, 'df_forecast.index')
        # print(df_forecast.loc[start_datetime_str_train:end_datetime_str_train])
        # print(df_forecast.loc[start_date_str_train:end_date_str_train], 'df_forecast')
        print(predict, 'predict')

        df_merge_concat = pd.concat([df_forecast, predict], axis=1)
        print(df_merge_concat, 'df_merge_concat')
        df_merge = df_merge_concat['value'].fillna(df_merge_concat['Prediction'])
        # print(df_merge.loc[start_date_str_train:end_date_str_train], 'df_merge2')
        # print(df_tmp)

        df_out = df_merge.resample('ME').sum()
        print(df_out, 'df_out')
        df_out.to_csv('df_out.csv')
        # df_out = df['value'].resample('ME').sum()
        # print(df_out, 'df_out2')
        # devicenya = df.iloc[0].to_dict() if not df.empty else {col: '' for col in df.columns}
        devicenya = df.iloc[0].to_dict()
        identity = {
            'id_device': devicenya.get('id_device', ''),
            'name_device': devicenya.get('name_device', ''),
            'id_customer': devicenya.get('id_customer', ''),
            'name_customer': devicenya.get('name_customer', ''),
        }
        print(df, 'df')
        print(df_merge_concat, 'df_merge_concat')

        return {
            'graph_month': df_out.fillna(0).to_list(),
            'graph_month_label': df_out.index.astype(str).to_list(),
            'graph_day': df_merge.fillna(0).to_list(),
            'graph_day_label': df_merge.index.astype(str).to_list(),
            'identity': identity
            # 'id_device': '',
            # 'name_device': '',
            # 'id_customer': '',
            # 'name_customer': '',
        }

async def main():
    conn = Connection()
    arima = ArimaModule()
    device_id = '1ee01383af6c0308c68d371b81349fd'
    sensor_key = 'usage2'

    start_date_str_tarik_data='2023-08-01'
    end_date_str_tarik_data='2023-12-20'

    start_date_str_train='2023-08-01'
    end_date_str_train='2023-12-20'

    start_date_str_test = '2023-12-21'
    end_date_str_test = '2023-12-31'

    start_date_str_wrap = '2023-12-01'
    end_date_str_wrap = '2023-12-31'
    df_history = await arima.get_data(conn, device_id, sensor_key, start_date_str_tarik_data, end_date_str_tarik_data)
    # df_history.to_pickle('df_history.pk')
    await conn.dispose_engines()

    # df_history = pd.read_pickle("df_history.pk")  
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
    # model_pk = os.path.join(os.getcwd(), 'arima_models', f"arima_{device_id}_{sensor_key}_{start_date_str_train}_{end_date_str_train}.pkl")
    # model = joblib.load(model_pk)
    # df_merge_pk = os.path.join(os.getcwd(), 'arima_models', f"df_merge_{device_id}_{sensor_key}_{start_date_str_train}_{end_date_str_train}.pkl")
    # model = joblib.load(model_pk)
    # df_merge = joblib.load(df_merge_pk)
    df_result = await arima.predict(model, start_date_str_test, end_date_str_test)
    # print(df_result[['Prediction']].sum())
    # print(df_merge, 'df_merge')

    await arima.wrapping_up(df_merge, df_result, start_date_str_wrap, end_date_str_wrap)
    df_historyx = df_merge['value'].resample('ME').sum()
    print(df_historyx, 'df_historyx2')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

