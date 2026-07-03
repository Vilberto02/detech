"""
Archivo de fixture para tests: contiene anomalias conocidas de todas las categorias.
Este archivo es intencional y solo para propositos de prueba de DETECH.
"""

import os, sys, json, re, math

password = "supersecreto123"
api_key = "sk-abc123xyz"

x = 5
ab = "hola"


def funcionMuyLarga():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    aa = 9
    bb = 10
    cc = 11
    dd = 12
    ee = 13
    ff = 14
    gg = 15
    hh = 16
    ii = 17
    jj = 18
    kk = 19
    ll = 20
    mm = 21
    nn = 22
    oo = 23
    pp = 24
    qq = 25
    rr = 26
    ss = 27
    tt = 28
    uu = 29
    vv = 30
    ww = 31
    xx = 32
    yy = 33
    zz = 34
    a1 = 35
    b1 = 36
    c1 = 37
    d1 = 38
    e1 = 39
    f1 = 40
    g1 = 41
    h1 = 42
    i1 = 43
    j1 = 44
    k1 = 45
    l1 = 46
    m1 = 47
    n1 = 48
    o1 = 49
    p1 = 50
    q1 = 51
    return a + q1


def funcion_sin_docstring(xa, ya, za, wa, va, ua):
    if xa > 0:
        if ya > 0:
            if za > 0:
                if wa > 0:
                    if va > 0:
                        return True
    return False


def funcion_con_eval(codigo):
    resultado = eval(codigo)
    return resultado


def consulta_sql(nombre_usuario):
    query = "SELECT * FROM usuarios WHERE nombre = '" + nombre_usuario + "'"
    return query


# TODO: Refactorizar antes del release
# FIXME: El manejo de errores es incompleto

# def funcion_comentada():
#     import antiguo_modulo
#     for item in lista:
#         procesar(item)
#     return resultado

linea_muy_larga = "Esta es una linea que supera los 79 caracteres de longitud maxima establecidos por PEP 8 de Python para codigo"
