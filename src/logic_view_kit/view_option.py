#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
# Copyright (c) 2026 ikwzm

class View_Option(dict):
    """ オプションを辞書で格納するためのクラス.

    dict クラスを継承し、階層構造を持つ辞書の深いコピー(Deep Copy) や
    マージ、特定のキーを持つ辞書の抽出を提供します.
    """

    def __init__(self, default=None, deep_copy=True):
        """ 初期化メソッド

        Args: 
            default (dict, optional): 初期データとなる辞書.
            deep_copy (boolean, optional): default のコピー方式を指定します.
                True  を指定した場合、default の「深いコピー(Deep Copy)」が作られます.
                False を指定した場合、default の「浅いコピー(Shallow Copy) 」が作られます.
        """
        if default is None:
            default = {}
        elif deep_copy:
            default = View_Option.deep_copy(default)
        super().__init__(default)
        
    def merge(self, add_dict):
        """ 指定した内容で上書きした「新しい」View_Option オブジェクトを作成して返します.

        Args:
            add_dict (dict or None): 上書きしたいキーと値を持つ辞書.

        Returns:
            View_Option: マージされた新しい View_Option オブジェクト.
                add_dict が None の場合は、上書きせずに自分自身(self) を返します.
                add_dict が None でない場合は、自分自身に add_dict をマージしたオブジェクトを返します.
                merge_dict() が結果を Deep Copy して返すため、View_Option の生成時には
                deep_copy=False を指定して不要なコピーを避けます。
        """
        if add_dict is not None:
            return View_Option(View_Option.merge_dict(self, add_dict), deep_copy=False)
        else:
            return self

    @staticmethod
    def deep_copy(obj):
        """ オブジェクトの「深いコピー(Deep Copy)」を作成します.

        辞書、リスト、タプル、セットの各階層を再帰的にコピーします.

        Args:
           obj (any): コピー対象のオブジェクト.

        Returns:
           any: 複製されたオブジェクト. 対応していない型はそのまま返します.
       """
        if isinstance(obj, dict):
            result = {}
            for key,value in obj.items():
                result[key] = View_Option.deep_copy(value)
            return result
        if isinstance(obj, list):
            result = []
            for value in obj:
                result.append(View_Option.deep_copy(value))
            return result
        if isinstance(obj, tuple):
            result = []
            for value in obj:
                result.append(View_Option.deep_copy(value))
            return tuple(result)
        if isinstance(obj, set):
            result = set()
            for value in obj:
                result.add(View_Option.deep_copy(value))
            return result
        return obj
        
    @staticmethod
    def new_dict(default=None):
        """ 新しい辞書 (dict) を作成します.

        Args:
            default (dict, optional): 元となる辞書.

        Returns:
            dict: default が None では無い場合は、その「深いコピー」を作って返します.
                  default が None の場合は空の辞書を返します.
        """
        if default is None:
            return {}
        else:
            return View_Option.deep_copy(default)
    
    @staticmethod
    def merge_dict(base, add_dict):
        """ 二つの辞書を再帰的にマージします.

        ベースとなる辞書の深いコピーを作成し、そこに add_dict の内容を上書きします.
        入れ子になった辞書同士は、さらに階層を掘り下げてマージされます.

        Args:
            base (dict): ベースとなる辞書.
            add_dict(dict or None): 追加・上書きする辞書.

        Returns:
            dict: マージされた新しい辞書.
        """
        base_dict = View_Option.new_dict(base)
        if add_dict is None:
            return base_dict
        for add_key, add_value in add_dict.items():
            if (add_key in base_dict and
                isinstance(add_value, dict) and
                isinstance(base_dict[add_key], dict)):
                base_dict[add_key] = View_Option.merge_dict(base_dict[add_key], add_value)
            else:
                base_dict[add_key] = View_Option.deep_copy(add_value)
        return base_dict

    @staticmethod
    def select_dict(source_dict, selector=None):
        """セレクター辞書に基づいて、元の辞書から特定のキーと値を抽出します.

        Args:
            source_dict (dict): 抽出元の辞書.
            selector (dict, optional): 抽出条件を指定する辞書.
               値が True のキー、または入れ子の構造が一致する部分を抽出します.

        Returns:
            dict: 抽出された新しい辞書.
        """
        new_dict = {}
        if isinstance(selector, dict):
            for key,value in selector.items():
                if key not in source_dict:
                    continue
                if value is True:
                    new_dict[key] = View_Option.deep_copy(source_dict[key])
                elif isinstance(value, dict) and isinstance(source_dict[key], dict):
                    new_dict[key] = View_Option.select_dict(source_dict[key], value)
        return new_dict

    def select(self, selector):
        """セレクター辞書に基づいて特定のオプションを抽出した「新しい」View_Option を作成します.

        Args:
            selector (dict): 抽出条件を指定する辞書.

        Returns:
            View_Option: 抽出されたデータを持つ新しい View_Option オブジェクト.
        """
        return View_Option(View_Option.select_dict(self, selector))
        
