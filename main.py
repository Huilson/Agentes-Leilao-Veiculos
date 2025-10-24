import re
import threading

from maspy import *
from listaCarros import carros


class PatioLeilao(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)
        self.create(Percept("aberto"))

    def receberCarro(self, src, carro):
        self.print(f"Recebi carro(s) do vendedor {src}")
        self.print(f"Carro: {carro}")
        carros.append(carro)

    def negociarCompraVenda(self, agt):
        self.print(f"Negociação iniciada para {agt}!")
        for carro in carros:
            self.print(f"Criando percepção: {carro['marca']}")
            self.create(Percept(carro["marca"], carro["vendedor"], adds_event= False))


class AgenteVendedor(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Belief("negociar"))
        self.add(Goal("vender"))
        #Carro do vendedor
        self.carro = {
            "marca": "prisma",
            "preco": 50000,
            "vendedor": self.agent_info()["my_name"]
        }

    @pl(gain, Goal("vender"), Belief("negociar"))
    def iniciarLeilao(self, src):
        self.print("Vou vender um carro")
        percepcao = self.get(Belief("aberto", source="patio"))
        if percepcao:
            patio.receberCarro(self.agent_info()["my_name"], self.carro)
            # agenda a negociação e a verificação do comprador
            threading.Timer(2.0, lambda: patio.negociarCompraVenda("AgenteComprador")).start()#CHATGPT fez essa linha

    @pl(gain, Belief("preco_de_compra", Any))
    def venderCarro(self, src, preco_de_compra):
        self.print(f"Recebi uma proposta: {preco_de_compra} do comprador {src}")
        if int(preco_de_compra) >= self.carro["preco"]:
            self.print(f"Carro vendido para {src}, obrigado!")
            for c in carros:
                if c["marca"] == "prisma":
                    carros.remove(c)
                    self.print(f"{c["marca"]} vendido, removendo carro da lista!")
                    break  # evita erro de iterar enquanto remove
            self.send(src, achieve, Goal("negocio_concluido"), "S2B")

        else:
            self.print("Preço abaixo do valor, podemos renegociar?")
            resposta = self.send(src, askOneReply, Belief("renegociar"), "S2B")
            if resposta:
                self.print("Renegociando...")
                self.send(src, tell, Belief("ver_nova_oferta", self.carro["preco"] * 0.9), "S2B")
            else:
                self.print("O {src} não aceita renegociar... Que pena")
        self.stop_cycle()


class AgenteComprador(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Goal("comprar"))
        self.add(Belief("renegociar"))
        self.orcamento = 45000

    @pl(gain, Goal("comprar"))
    def verCarros(self, src):
        self.connect_to(Environment("patio"))
        self.print("Comprador aguardando negociação...")
        # agenda verificação da percepção 3 segundos depois (tempo suficiente para negociar)
        threading.Timer(3.0, self.verificarCarro).start()#Solução do GPT para esperar que todos os vendedores
        #postem seus carros antes dos compradores irem até o Ambiente para ver os carros disponíveis

    @pl(gain, Goal("negocio_concluido"))
    def compraFinalizada(self, src):
        self.print("Oba! Conseguimos comprar o carro desejado!")
        self.stop_cycle()

    @pl(gain, Belief("ver_nova_oferta", Any))
    def verOferta(self, src, ver_nova_oferta):
            self.print(f"O {src} não aceitou o valor, ele somente aceita {ver_nova_oferta}")
            if int(ver_nova_oferta) <= self.orcamento:
                self.print(f"Vou aceitar a nova oferta do {src} ")
                self.print("Oba! Conseguimos comprar o carro desejado!")
                for c in carros:
                    if c["marca"] == "prisma":
                        carros.remove(c)
                        self.print(f"{c["marca"]} foi comprado, removendo carro da lista!")
                        break  # evita erro de iterar enquanto remove
            else:
                self.print(f"Valor ainda é muito alto, que pena...")
            self.stop_cycle()

    def verificarCarro(self): #CHATGPT ajudou aqui
        percepcao = self.get(Belief("prisma", Any, source="patio"))
        vendedor = re.search(r'\((.*?)\)', str(percepcao)).group(1)# Expressão regular feita pelo GPT
        if percepcao:
            self.print(f"Ok!!! O carro desejado está disponível para compra.")
            self.print(f"O vendedor é {vendedor}... entrando em contanto...")
            self.send(vendedor, tell, Belief("preco_de_compra", self.orcamento), "S2B")
        else:
            self.print("O carro desejado não foi encontrado, sinto muito...")
            self.stop_cycle()


# ===============================
Admin().set_logging(show_exec=True)
vendedor = AgenteVendedor("AgenteVendedor")
comprador = AgenteComprador("AgenteComprador")
patio = PatioLeilao("patio")
canal = Channel("S2B")

Admin().connect_to([comprador, vendedor], [canal, patio])
Admin().report = True
Admin().start_system()
