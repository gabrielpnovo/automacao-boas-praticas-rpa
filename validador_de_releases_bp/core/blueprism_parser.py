from .xml_utils import get_root_xml
from .constants import NAMESPACES as ns
from .models import BPProcess, BPObject
import xml.etree.ElementTree as ET

def extrai_processos_e_objetos(root):
    processos = []
    objetos = []

    process_groups = root.findall(".//procgrp:process-group", ns)
    object_groups = root.findall(".//objgrp:object-group", ns)

    for group in process_groups:
        for member in group.findall(".//procgrp:members/procgrp:process", ns):
            pid = member.get("id")
            if pid:
                proc = root.find(f".//proc:process[@id='{pid}']", ns)
                if proc is not None and proc.get("name"):
                    processos.append(BPProcess(
                        id=pid,
                        name=proc.get("name"),
                        root=proc
                    ))

    for group in object_groups:
        for member in group.findall(".//objgrp:members/objgrp:object", ns):
            oid = member.get("id")
            if oid:
                obj = root.find(f".//obj:object[@id='{oid}']", ns) or root.find(f".//proc:object[@id='{oid}']", ns)
                if obj is not None and obj.get("name"):
                    objetos.append(BPObject(
                        id=oid,
                        name=obj.get("name"),
                        root=obj
                    ))

    return processos, objetos
