import logging

from pyasn1.type import univ
from pysnmp.proto import rfc1902

LOG = logging.getLogger(__name__)


class ScalarInstanceFactory(object):
    @staticmethod
    def build(name, base_class, impl_class):
        def __init__(self, *args, **kwargs):
            self.impl_class = impl_class
            base_class.__init__(self, *args, **kwargs)

        def __read_get__(self, name, val, idx, acInfo):
            engine = acInfo[1]

            if engine.unity_client == None:
                LOG.info(
                    'Reconnecting to unity: {}, agent port: {}'.format(
                        engine.parent.array_config.mgmt_ip,
                        engine.parent.port))
                engine.parent.connect_backend_device()

            if engine.unity_client == None:
                LOG.info(
                    'Failed to reconnect unity: {}, agent port: {}'.format(
                        engine.parent.array_config.mgmt_ip,
                        engine.parent.port))
                return name, self.getSyntax().clone()

            idx_len = self.instId[0]
            idx_name = ''.join([chr(x) for x in self.instId[1: idx_len + 1]])

            try:
                return name, self.getSyntax().clone(
                    self.impl_class().read_get(name, idx_name,
                                               engine.unity_client)
                )
            except:
                # TODO: logging ...
                return name, self.getSyntax().clone()
                # raise

        newclass = type(name + "ScalarInstance", (base_class,),
                        {"__init__": __init__,
                         "readGet": __read_get__
                         })
        return newclass


class TableColumnInstanceFactory(object):
    @staticmethod
    def build(name, base_class, proto_inst, entry, impl_class):
        def __init__(self, *args, **kwargs):
            self.entry = entry
            self.impl_class = impl_class
            self.maxAccess = 'readcreate'
            base_class.__init__(self, *args, **kwargs)

        def __read_getnext__(self, name, val, idx, acInfo, oName=None):
            engine = acInfo[1]
            if engine.unity_client == None:
                LOG.info(
                    'Reconnecting to unity: {}, agent port: {}'.format(
                        engine.parent.array_config.mgmt_ip,
                        engine.parent.port))
                engine.parent.connect_backend_device()

            if engine.unity_client == None:
                LOG.info(
                    'Failed to reconnect unity: {}, agent port: {}'.format(
                        engine.parent.array_config.mgmt_ip,
                        engine.parent.port))
                # TODO: need to consider how to handle this scenario
                return

            if self.name == name:
                row_list = self.impl_class().get_idx(name, idx,
                                                     engine.unity_client)
                # Destory table rows, otherwise deleted items exist in table
                self.unregisterSubtrees(*self._vars.keys())
                for row in row_list:
                    row_instance_id = self.entry.getInstIdFromIndices(row)
                    # Create table row and set default value
                    # DisplayString: null, Integer32: 0
                    # Only two types of data now: DisplayString, Integer32
                    # If new data types added, need to consider how to set val
                    if isinstance(val, univ.Null) and isinstance(self.syntax,
                                                                 rfc1902.Integer32):
                        val = 0
                    self.createTest(name + row_instance_id, val, idx, acInfo)
                    self.createCommit(name + row_instance_id, val, idx, acInfo)
            next_node = self.getNextNode(name, idx)
            return next_node.readGet(next_node.name, val, idx, acInfo)

        newclass = type(name + "Instance", (base_class,),
                        {"__init__": __init__,
                         "protoInstance": proto_inst,
                         "readGetNext": __read_getnext__})
        return newclass
