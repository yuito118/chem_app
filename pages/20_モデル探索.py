from pathlib import Path
import sys
import streamlit as st
import pandas as pd
# 親のmodule群をimportできるように
sys.path.append(str(Path(__file__).resolve().parent.parent))
from components.DownloadLink import DownloadLink
from components import Divider
from modules.ModelSearcher import ModelSearcher
from modules.Models.Models import ModelList
from modules.Graph import Graph

st.title('モデル探索')

st.subheader('1. csvアップロード')
csv = st.file_uploader(label='csv', type='csv', label_visibility='hidden', key='csv')
df = pd.DataFrame()
if (csv):
    df = pd.read_csv(csv)
    st.write(f'csvのサイズ: {df.shape}')
    st.dataframe(df)

    st.subheader('2. 目的変数を選択')
    target = st.selectbox(
        key='target',
        label='target',
        label_visibility='hidden',
        options=(df.columns)
    )
    
    st.subheader('3. モデルを選択')
    models = st.multiselect(
        key='models', label='models', label_visibility='hidden',
        options=ModelList.get_keys(),
        default=[]
    )

    isDCV = st.checkbox(label='DCVを使用するか？(*データ数30以上の場合非推奨)', key='isDCV', value=False)
    preprocessing = st.checkbox(label='特徴量選択を行うか？(*DCVの場合不可)', key='preprocessing', value=False, disabled=isDCV)

    Divider.render()

    detail = pd.DataFrame([],columns=['model', 'test_r2', 'test_mae', 'test_rmse', 'train_r2', 'train_mae', 'train_rmse'])
    clicked = st.button(label='モデルを探索する', type='primary', disabled=(csv == None))
    if clicked:
        for model in models:
            st.subheader(f'{model}の結果')
            results = ModelSearcher(df, target, model, isDCV, preprocessing).exec()
            if not isDCV:
                col1, col2 = st.columns(2)
                st.write(f'best_params：{results["best_params"]}')

                train_fig = Graph(obs=results['y_train'], pred=results['y_predict_train'], title='train').yyplot()
                test_fig = Graph(obs=results['y_test'], pred=results['y_predict'], title='test').yyplot()
                with col1:
                    st.pyplot(train_fig)
                with col2:
                    st.pyplot(test_fig)

            results_df = pd.DataFrame([
                [results['train_r2'], results['test_r2']],
                [results['train_mae'], results['test_mae']],
                [results['train_rmse'], results['test_rmse']],
            ], columns=['train', 'test'], index=['r2', 'mae', 'rmse'])
            st.dataframe(results_df)
            
            detail = detail.append({
                'model': model,
                'test_r2': results['test_r2'], 'test_mae': results['test_mae'], 'test_rmse': results['test_rmse'],
                'train_r2': results['train_r2'], 'train_mae': results['train_mae'], 'train_rmse': results['train_rmse'],
            }, ignore_index=True)

        st.header('結果')
        DownloadLink.display(csv=df.to_csv(index=False), filename='モデル探索結果')
        st.dataframe(detail)

