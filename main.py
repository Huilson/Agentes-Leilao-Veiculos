import ast
import random
import re
import threading

from maspy import *
from listaCarros import carros

carrosPatio = []

class Patio(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)
        self.create(Percept("aberto"))#Abre o leilão
        self.carroMarca = []
        self.melhorPreco = float('inf')
        self.melhorCarro = {}

    #Essa função simula os carros que vão entrando para leilão
    def receberCarro(self, src, carro):
        self.print(f"Recebi carro(s) do vendedor {src}")
        self.print(f"Carro: {carro}")
        carrosPatio.append(carro)

    #Conecta os possíveis compradores e o vendedores
    def negociarCompraVenda(self, agt):
        self.print(f"Negociação iniciada para {agt}!")
        for carro in carrosPatio:
            if carro['marca'] not in self.carroMarca:
                if carro['preco'] <= self.melhorPreco:
                    self.melhorPreco = carro['preco']
                    self.melhorCarro = carro
                self.carroMarca.append(carro['marca'])
                self.print(f"Criando percepção: {carro['marca']}")
                #Percepção chave, graças a essa percepção que o comprador saberá quem tem o carro que ele deseja pelo
                #menor preço. O nome da percepção leva a marca do carro, e o valor dessa percepção é o nome do vendedor
            self.create(Percept(self.melhorCarro['marca'], self.melhorCarro, adds_event= False))

            #seria legal mandar uma percepção para os vendedores que não tiveram seus carros escolhidos
            #para dar um stop_cycle(), só precisa refinar a lógica


class AgenteVendedor(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Belief("negociar"))
        self.add(Goal("vender"))

        #Sorteia um número, pega da lista de carros, usado para simular um carro para vender
        num = random.randint(0, 2)
        self.carro = carros[num]
        self.carro["vendedor"] = self.agent_info()["my_name"] #Adiciona o nome do Agente Vendedor

    @pl(gain, Goal("vender"), Belief("negociar"))
    def iniciarLeilao(self, src):
        #O vendedor já começa querendo vender um carro
        self.print("Vou vender um carro")
        percepcao = self.get(Belief("aberto", source="patio"))
        #Se o pátio do leilão estiver aberto, ele pode enviar seu carro para vender
        if percepcao:
            # O carro tem como chave o nome do vendedor, chave = nome do vendedor; valor = detalhe do carro (dicionário)
            patio.receberCarro(self.agent_info()["my_name"], self.carro)# "Envia" o carro para o ambiente
            # agenda a negociação e a verificação do comprador
            threading.Timer(2.0, lambda: patio.negociarCompraVenda("AgenteComprador")).start()#CHATGPT fez essa linha

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

    @pl(gain, Belief("acabou"))
    def semComprador(self, src):
        # Essa função é uma saída genérica para caso nade de certo
        self.print("A negociação não foi finalizada por algum motivo, encerrando...")
        self.stop_cycle()

class AgenteComprador(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Goal("comprar"))
        self.orcamento = 45000 #Limite de quanto gastar
        #Variáveis de controle
        self.vendedor = ""
        self.preco = ""
        self.listaCompra = []

    @pl(gain, Goal("comprar"))
    def verCarros(self, src):
        self.connect_to(Environment("patio"))
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
                self.send("AgenteVendedor", tell, Belief("acabou"), "S2B")
            self.stop_cycle()

    def verificarCarro(self): #CHATGPT ajudou aqui
        #Essa função é usada para verificar se o carro desejado pelo comprador está no pátio (ambiente)
        percepcao = self.get(Belief("prisma", Any, source="patio"))

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
            self.send("AgenteVendedor_1", tell, Belief("acabou"), "S2B")
            #self.stop_cycle()

    #Precisa melhor o encerramento dos agentes, infelizmente não consigo pensar em uma forma legal de fazer isso.


# ===============================
#Admin().set_logging(show_exec=True)
vendedor1 = AgenteVendedor("AgenteVendedor")
vendedor2 = AgenteVendedor("AgenteVendedor")
comprador = AgenteComprador("AgenteComprador")

comprador.add(Belief("renegociar"))#Remova essa linha caso não deseje renegociar

patio = Patio("patio")
canal = Channel("S2B")

Admin().connect_to([comprador, vendedor1, vendedor2], [canal, patio])
Admin().report = True
Admin().start_system()