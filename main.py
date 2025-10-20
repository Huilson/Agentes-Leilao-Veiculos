from maspy import *
import random

class MonitoramentoUrbano(Environment):
    def __init__(self, env_name):
        super().__init__(env_name)
        self.create(Percept("tem_obstaculo"))

    def desviar_obstaculo(self, src):
        desvio = random.choice([True, False])
        print(desvio)
        if desvio:
            self.print("Obstáculo desviado!")
            self.create(Percept("obstaculo_resolvido"))
        else:
            self.print("Obstáculo não desviado!")
            self.create(Percept("obstaculo_nao_resolvido"))


class VA(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)
        self.add(Belief("conduzindoVA"))

    @pl(gain, Belief("conduzindoVA"))
    def verifica_via_urbana(self, src):
        self.print("Verificar via urbana")
        percepcao1 = self.get(Belief("tem_obstaculo", source="BR101"))
        self.print(percepcao1.key)
        if percepcao1:
            self.desviar_obstaculo()
            self.perceive("BR101")
            self.add(Goal("verificar_acao"))

    @pl(gain, Goal("verificar_acao"), Belief("conduzindoVA"))
    def verificar_acao(self, src):
        percepcao2 = self.get(Belief("obstaculo_resolvido", source="BR101"))
        percepcao3 = self.get(Belief("obstaculo_nao_resolvido", source="BR101"))
        if percepcao2:
            self.print("Desvio realizado com sucesso!")
            self.send("ControladorRemoto", tell, Belief("VA_operacional"))
            self.stop_cycle()
        elif percepcao3:
            self.add(Belief("obstaculo"))
            self.add(Goal("manobraCritica"))
        else:
            self.add(Goal("verificar_acao"))

    @pl(gain, Goal("manobraCritica"), Belief("obstaculo"))
    def avisar_stakeholder(self, src):
        # envia msg para o agente Stakeholder
        self.print("Manobra crítica; Acionar stakeholder")
        self.send("ControladorRemoto", tell, Belief("VA_precisa_ajuda"), "V2C")

    @pl(gain, Goal("manobraEmergencia"))
    def executar_manobra(self, src):
        self.print(f"Manobra executada conforme stakeholder: {src}")
        self.stop_cycle()


class Stakeholder(Agent):
    def __init__(self, agt_name):
        super().__init__(agt_name)

    @pl(gain, Belief("VA_precisa_ajuda"))
    def enviar_manobra(self, src):
        # envia msg para agente Waymo (VA)
        self.send("Waymo", achieve, Goal("manobraEmergencia"), "V2C")
        self.stop_cycle()

    @pl(gain, Belief("VA_operacional"))
    def desligar(self, src):
        self.stop_cycle()


if __name__ == "__main__":
    monitor = MonitoramentoUrbano("BR101")
    veiculo = VA("Waymo")
    controlador = Stakeholder("ControladorRemoto")
    comunicacao_ch = Channel("V2C")
    Admin().connect_to([veiculo, controlador], comunicacao_ch)
    Admin().report = True
    Admin().start_system()
