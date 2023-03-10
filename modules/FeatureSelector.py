from enum import Enum
import pandas as pd
import numpy as np
from sklearn.feature_selection import VarianceThreshold
from sklearn.ensemble import RandomForestRegressor
from boruta import BorutaPy
from typing import List

class Methods(Enum):
    variance = "分散"
    corr = "相関(類似データを削除)"
    boruta = "ボルタ(時間がかかります)"

    @classmethod
    def get_values(cls):
        return [i.value for i in cls]
    
    def get_value(self):
        return self.value

class FeatureSelector():
    def __init__(self, X: pd.DataFrame, y: pd.DataFrame, hidden_columns: List[str], methods: Methods) -> None:
        _X = X.dropna().reset_index(drop=True)
        self.X = _X.drop(columns=hidden_columns)
        self.y = y
        self.methods = methods
        self.hidden_df = _X[hidden_columns]

    def select(self) -> pd.DataFrame:
        if Methods.variance.value in self.methods: self.removeVariance()
        if Methods.corr.value in self.methods: self.removeHighCorr()
        if Methods.boruta.value in self.methods: self.boruta()
        result_df = pd.concat([self.hidden_df, self.X, self.y], axis=1)
        return result_df

    def removeVariance(self) -> None:
        select = self.getVarianceThreshold()
        select.fit_transform(self.X.values)
        selected_columns = self.X.columns[select.get_support()]
        self.X = pd.DataFrame(self.X[selected_columns], columns=selected_columns)

    @staticmethod
    def getVarianceThreshold() -> VarianceThreshold:
        # ベルヌーイ分布に基づく分散の閾値は0.16
        return VarianceThreshold(threshold=(.8 * (1 - .8)))

    def removeHighCorr(self) -> None:
        threshold = 0.95
        df_corr = abs(self.X.corr())
        columns = df_corr.columns
        
        # 対角線の値を0にする
        for i in range(0,len(columns)):
            df_corr.iloc[i,i] = 0

        while True:
            columns = df_corr.columns
            max_corr = 0.0
            query_column = None
            target_column = None

            df_max_column_value = df_corr.max()
            max_corr = df_max_column_value.max()
            query_column = df_max_column_value.idxmax()
            target_column = df_corr[query_column].idxmax()

            if max_corr < threshold:
                # しきい値を超えるものがなかったため終了
                break
            else:
                # しきい値を超えるものがあった場合
                delete_column = None
                saved_column = None

                # その他との相関の絶対値が大きい方を除去
                if sum(df_corr[query_column]) <= sum(df_corr[target_column]):
                    delete_column = target_column
                    saved_column = query_column
                else:
                    delete_column = query_column
                    saved_column = target_column

                # 除去すべき特徴を相関行列から消す（行、列）
                df_corr.drop([delete_column], axis=0, inplace=True)
                df_corr.drop([delete_column], axis=1, inplace=True)

        self.X = self.X[df_corr.columns]
        
    def boruta(self):
        # RandomForestRegressorでBorutaを実行
        boruta_selector = self.getBoruta()
        boruta_selector.fit(self.X.values, self.y.values)

        # 選択された特徴量を確認
        selected = boruta_selector.support_
        print(f'選択された特徴量の数: {np.sum(selected)}')
        print(self.X.columns[selected])

        self.X = self.X[self.X.columns[selected]]

    @staticmethod
    def getBoruta(perc=70) -> BorutaPy:
        rf = RandomForestRegressor(n_jobs=-1, max_depth=5)
        boruta_selector = BorutaPy(
            rf,
            n_estimators='auto',
            verbose=2,
            alpha=0.05,    # 有意水準
            max_iter=100,  # 試行回数
            perc=perc,       # ランダム生成変数の重要度の何％を基準とするか。70~80が良さそう
            random_state=42
        )
        return boruta_selector