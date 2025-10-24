import ast
import re
import threading

from maspy import *
from listaCarros import carros

class AgenteComprador(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Goal("comprar"))
        self.orcamento = 45000 #Limite de quanto gastar
        #Variáveis de controle
        self.carroDesejado = "prisma"
        self.vendedor = ""
        self.preco = ""
        self.listaCompra = []

    @pl(gain, Goal("comprar"))
    def verCarros(self, src):
        self.connect_to(Environment("Patio"))
        self.print("Comprador aguardando negociação...")
        # Solução do GPT para esperar que todos os vendedores postem seus carros antes dos compradores irem até o
        # Ambiente para ver os carros disponíveis
        # Agenda verificação da percepção 5 segundos depois (tempo suficiente para negociar)
        threading.Timer(5.0, self.verificarCarro).start()

    @pl(gain, Goal("negocio_concluido"))
    def compraFinalizada(self, src):
        #Melhor cenário, o carro foi comprado
        self.print("Oba! Conseguimos comprar o carro desejado!")
        self.stop_cycle()

    @pl(gain, Belief("ver_nova_oferta", Any))
    def verOferta(self, src, ver_nova_oferta):
            #Essa crença é dada pelo vendedor, mas somente se o comprador tiver a crença de renegociar
            self.print(f"O {src} não aceitou o valor, ele somente aceita {ver_nova_oferta}")
            if int(ver_nova_oferta) <= self.orcamento: #se a nova oferta ainda estiver dentro do orçamento
                self.print(f"Vou aceitar a nova oferta do {src} ")
                #repete o processo de remover o carro da lista (isso foi visto lá no vendedor)
                self.print("Oba! Conseguimos comprar o carro desejado!")
                for c in carros:
                    if c["marca"] == "prisma":
                        carros.remove(c)
                        self.print(f"{c["marca"]} foi comprado, removendo carro da lista!")
                        break  # evita erro de iterar enquanto remove
            else:#Pior cenário, o carro não foi vendido
                self.print(f"Valor ainda é muito alto, que pena...")
                self.send("AgenteVendedor_1", tell, Belief("finalizar"), "S2B")
                self.send("AgenteVendedor_2", tell, Belief("finalizar"), "S2B")
                self.send("AgenteVendedor_3", tell, Belief("finalizar"), "S2B")
            self.stop_cycle()

    def verificarCarro(self): #CHATGPT ajudou aqui
        #Essa função é usada para verificar se o carro desejado pelo comprador está no pátio (ambiente)
        percepcao = self.get(Belief(self.carroDesejado, Any, source="Patio"))

        #---Essa parte foi o chat que fez---#
        #Ele basicamente, desmonta a string e remonta o dicionário
        match = re.search(r"\((\{.*\})\)", str(percepcao))
        if match:
            conteudo = match.group(1)  # {'marca': 'prisma', 'ano': 2015, ...}
            carro = ast.literal_eval(conteudo)  # converte para dict
            self.preco = carro["preco"]
            self.vendedor = carro["vendedor"]

            self.listaCompra.append((self.vendedor, self.preco))

            print(f"Preço: {self.preco}, Vendedor: {self.vendedor}")
        else:
            print("Nenhum dicionário encontrado.")
        #-----------------------------------#

        if percepcao:
            # Usei a expressão acima para extrair o nome do agente vendedor
            self.print(f"Ok! O carro desejado está disponível para compra.")
            self.print(f"O vendedor é {self.vendedor}... entrando em contanto...")
            #Manda uma crença para o vendedor, avisando que os dois tem interesse no mesmo carro
            #Essa crença envia a primeira oferta do comprador
            self.send(self.vendedor, tell, Belief("preco_de_compra", self.orcamento), "S2B")
        else:
            self.print("O carro desejado não foi encontrado, sinto muito...")
            self.send("AgenteVendedor_1", tell, Belief("finalizar"), "S2B")
            self.send("AgenteVendedor_2", tell, Belief("finalizar"), "S2B")
            self.send("AgenteVendedor_3", tell, Belief("finalizar"), "S2B")
            self.stop_cycle()

    #Precisa melhor o encerramento dos agentes, infelizmente não consigo pensar em uma forma legal de fazer isso.