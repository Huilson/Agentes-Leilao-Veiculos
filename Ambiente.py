import threading
from maspy import *

carrosPatio = []
lock = threading.Lock()#GPT

class Patio(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)
        self.create(Percept("aberto"))
        self.carros_por_marca = {}

    #Essa função simula os carros que vão entrando para leilão
    def receberCarro(self, src, carro):
        with lock:#GPT
            self.print(f"Recebi carro(s) do vendedor {src}")
            self.print(f"Carro: {carro}")
            carrosPatio.append(carro)

    #Conecta os possíveis compradores e o vendedores
    def negociarCompraVenda(self, agt):
        #O comprador só tem acesso a essa informação quando seu temporizador acabar
        self.print(f"Negociação iniciada para {agt}!")

        for carro in carrosPatio:#Ordenar carros, e separar a marca com o menor valor
            marca = carro["marca"]
            preco = carro["preco"]
            if marca not in self.carros_por_marca or preco < self.carros_por_marca[marca]["preco"]:
                self.carros_por_marca[marca] = carro
        menores_valores = list(self.carros_por_marca.values())
        self.print(f"Os melhores carros são: {menores_valores}")

        for carro in menores_valores:
            self.create(Percept(carro['marca'], carro, adds_event= False))

            #seria legal mandar uma percepção para os vendedores que não tiveram seus carros escolhidos
            #para dar um stop_cycle(), só precisa refinar a lógica