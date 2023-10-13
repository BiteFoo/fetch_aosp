# coding:utf8
'''
@File    :   libs.py
@Author  :   Loopher 
@Version :   1.0
@date    :    2023/10/12 17:53:04
@License :   (C)Copyright 2020-2021,Loopher
@Desc    :   None
'''


class Numeric():
    def __init__(self, message, base=10, lbound=None, ubound=None):
        self.message = message
        self.base = base
        self.lbound = lbound
        self.ubound = ubound

    def ask(self):
        try:
            answer = int(input(self.message + ' '), self.base)
            if self.lbound is not None:
                if answer < self.lbound:
                    return self.ask()
            if self.ubound is not None:
                if answer > self.ubound:
                    return self.ask()
            return answer
        except ValueError:
            return self.ask()
