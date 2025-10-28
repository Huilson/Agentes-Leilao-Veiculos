import random
import threading

from maspy import *

from Ambiente import Patio
from listaCarros import carros


class AgenteVendedor(Agent):
    def __init__(self, agt_name, patio_instance):
        super().__init__(agt_name)
        self.add(Belief("negociar"))
        self.add(Goal("vender"))
        self.patio = patio_instance

        #Sorteia um número, pega da lista de carros, usado para simular um carro para vender
        num = random.randint(0, 9)
        self.carro = carros[num]
        self.carro["vendedor"] = self.agent_info()["my_name"] #Adiciona o nome do Agente Vendedor

    @pl(gain, Goal("vender"), Belief("negociar"))
    def enviarCarro(self, src):
        #O vendedor já começa querendo vender um carro
        self.print(f"{self.my_name} vou vender um carro!")
        percepcao = self.get(Belief("aberto", source="Patio"))
        #Se o pátio do leilão estiver aberto, ele pode enviar seu carro para vender
        if percepcao:
            # O carro tem como chave o nome do vendedor, chave = nome do vendedor; valor = detalhe do carro (dicionário)
            self.patio.receberCarro(self.my_name, self.carro)# "Envia" o carro para o ambiente
            # agenda a negociação e a verificação do comprador
            threading.Timer(2.0, lambda: self.patio.negociarCompraVenda("AgenteComprador")).start()#CHATGPT fez essa linha

    @pl(gain, Belief("preco_de_compra", Any))
    def venderCarro(self, src, preco_de_compra):
        #Caso algum vendedor tenha interesse no carro do vendedor, é preciso verificar os preços de ambos os lados
        self.print(f"Recebi uma proposta: {preco_de_compra} do comprador {src}")
        if int(preco_de_compra) >= self.carro["preco"]:
            #Esse é o melhor cenário, onde a oferta do comprador é aceita de primeira
            self.print(f"Carro vendido para {src}, obrigado!")
            #Remove o carro da lista (no caso se tivesse um banco de dados, iria remover do banco)
            for c in carros:
                if c["marca"] == "prisma":
                    carros.remove(c)
                    self.print(f"{c["marca"]} vendido, removendo carro da lista!")
                    break  # evita erro de iterar enquanto remove
            self.send(src, achieve, Goal("negocio_concluido"), "S2B")#Avisa o comprador que tudo deu certo

        else:
            #Esse é o cenário intermediário, onde a oferta do comprador não foi aceita de primeira
            self.print("Preço abaixo do valor, podemos renegociar?")
            resposta = self.send(src, askOneReply, Belief("renegociar"), "S2B") #verifica se o comprador deseja renegociar
            if resposta:
                #Se o comprador tiver a crença de renegociar uma nova oferta é enviada
                self.print("Renegociando...")
                #Envia uma nova crença, essa crença permite o comprador ter mais uma chance de comprar o carro com um desconto
                self.send(src, tell, Belief("ver_nova_oferta", self.carro["preco"] * 0.9), "S2B")#10% de desconto
            else:
                self.print("O {src} não aceita renegociar... Que pena")#Esse é o pior cenário, onde o carro não é vendido
        self.stop_cycle()

    @pl(gain, Goal("finalizar"))
    def semComprador(self, src):
        # Essa função é uma saída genérica para caso nade de certo
        self.print("A negociação não foi finalizada por algum motivo, encerrando...")
        self.stop_cycle()