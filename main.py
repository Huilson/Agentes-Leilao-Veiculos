from maspy import *


class AgenteVendedor(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Belief("negociar"))
        self.add(Goal("vender"))

    @pl(gain, Goal("vender"), Belief("negociar"))
    def iniciarLeilao(self, src):
        self.print("Vou vender um carro")
        self.send("AgenteComprador", tell, Belief("temCarro",5), "S2B")

    @pl(gain, Goal("negociar", Any))
    def venderCarro(self, src, negociar):
        self.print(f"{src} quer comprar meu carro... OK! Valor: R${negociar}")
        self.stop_cycle()


class AgenteComprador(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)

    @pl(gain, Belief("temCarro", Any))
    def comprarCarro(self, src, temCarro):
        self.print(f"O {src} tem um carro disponivel para que eu possa comprar, Quantidade: {temCarro}")
        self.send("AgenteVendedor", achieve, Goal("negociar", 50000), "S2B")
        self.stop_cycle()


comprador = AgenteComprador("AgenteComprador")
vendedor = AgenteVendedor("AgenteVendedor")
canal = Channel("S2B")
Admin().connect_to([comprador, vendedor], canal)
Admin().report = True
Admin().start_system()
