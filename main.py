import threading
from maspy import *

carros = [] #simulação de um banco de dados

class PatioLeilao(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)
        self.create(Percept("aberto"))

    def receberCarro(self, src, carro):
        self.print(f"Recebi carro(s) do vendedor {src}")
        self.print(f"Carro: {carro}")
        carros.append(carro)

    def negociarCompraVenda(self, agt):
        self.print(f"deu certo {agt}!")
        for carro in carros:
            self.print(f"Criando percepções {carro["marca"]}")
            self.create(Percept(carro["marca"]))


class AgenteVendedor(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Belief("negociar"))
        self.add(Goal("vender"))

    @pl(gain, Goal("vender"), Belief("negociar"))
    def iniciarLeilao(self, src):
        carro = {
            "marca" : "prisma",
            "preco" : 50000,
            "quantidade" : 2,
            "vendedor" : self.agent_info()["my_name"]
        }
        self.print("Vou vender um carro")
        #self.send("AgenteComprador", tell, Belief("temCarro",carro), "S2B")
        percepcao = self.get(Belief("aberto", source="patio"))
        if percepcao:
            self.receberCarro(carro)

#    @pl(gain, Goal("negociar", Any))
 #   def venderCarro(self, src, negociar):
  #      self.print(f"{src} quer comprar meu carro... OK! Valor: R${negociar}")
   #     self.stop_cycle()


class AgenteComprador(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Goal("comprar"))

    @pl(gain, Goal("comprar"))
    def verCarros(self, src):
        self.connect_to(Environment("patio"))
        threading.Timer(10.0, self.negociarCompraVenda).start()

    #@pl(gain, Belief("temCarro", Any))
    #def comprarCarro(self, src, temCarro):
        #self.print(f"O {src} tem um carro disponivel para que eu possa comprar, Quantidade: {temCarro}")
        #self.send("AgenteVendedor", achieve, Goal("negociar", 50000), "S2B")
        #self.stop_cycle()


vendedor = AgenteVendedor("AgenteVendedor")
comprador = AgenteComprador("AgenteComprador")
patio = PatioLeilao("patio")
canal = Channel("S2B")
Admin().connect_to([comprador, vendedor], [canal, patio])
Admin().report = True
Admin().start_system()
