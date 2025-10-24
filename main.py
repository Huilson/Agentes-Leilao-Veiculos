from maspy import *

from AgenteComprador import AgenteComprador
from AgenteVendedor import AgenteVendedor
from Ambiente import Patio

# ===============================
patio = Patio("Patio")
canal = Channel("S2B")

vendedor1 = AgenteVendedor("AgenteVendedor")
vendedor2 = AgenteVendedor("AgenteVendedor")
vendedor3 = AgenteVendedor("AgenteVendedor")
comprador = AgenteComprador("AgenteComprador")
comprador.add(Belief("renegociar"))#se ele aceita ou não renegociar

# conectar todos de uma vez
Admin().connect_to([comprador, vendedor1, vendedor2, vendedor3], [canal, patio])
Admin().report = True

# só inicia o sistema depois que todos foram criados e conectados
Admin().start_system()