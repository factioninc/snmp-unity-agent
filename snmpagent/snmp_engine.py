import factory
from parsers.mib_parser import get_mib_symbols
from pysnmp import debug
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.proto.api import v2c
from pysnmp.smi import builder
from unityImpl.agent_info import AgentInfo
from unityImpl.enclosure_table import EnclosureTableInfo

debug.setLogger(debug.Debug('all'))


class SNMPEngine(object):
    def __init__(self):
        # Create SNMP engine
        self.snmp_engine = engine.SnmpEngine()

        snmp_context = context.SnmpContext(self.snmp_engine)
        self.mib_builder = snmp_context.getMibInstrum().getMibBuilder()

        # mibSources = self.mib_builder.getMibSources() + (builder.DirMibSource('.'),)
        # self.mib_builder.setMibSources(*mibSources)

        mibSources = self.mib_builder.getMibSources()
        self.mib_builder.setMibSources(builder.DirMibSource('./mibs/'),
                                       *mibSources)

        self.MibScalar, self.MibTableColumn, self.MibTableRow, self.MibScalarInstance = self.mib_builder.importSymbols(
            'SNMPv2-SMI', 'MibScalar', 'MibTableColumn', 'MibTableRow', 'MibScalarInstance'
        )

    def addTransport(self, ip, port, idx=0):
        # Transport setup
        # UDP over IPv4
        config.addTransport(self.snmp_engine,
                            udp.domainName + (idx,),
                            udp.UdpTransport().openServerMode((ip, port)))

    def addV3User(self, user_name, auth_protocol, auth_key,
                  priv_protocol, priv_key, security_engineId=None,
                  security_name=None):
        config.addV3User(self.snmp_engine, user_name, auth_protocol, auth_key,
                         priv_protocol, priv_key, security_engineId,
                         security_name)

    def addV1System(self, community_index, community_name,
                    context_engine_id=None, context_name=None,
                    transport_tag=None, security_name=None):
        config.addV1System(self.snmp_engine, community_index, community_name,
                           context_engine_id, context_name,
                           transport_tag, security_name)

    def addVacmUser(self, security_model, security_name, security_level,
                    read_sub_tree=(), write_sub_tree=(), notify_sub_tree=()):
        # Allow read MIB access for this user / securityModels at VACM
        config.addVacmUser(self.snmp_engine, security_model, security_name,
                           security_level, read_sub_tree, write_sub_tree,
                           notify_sub_tree)

    def registerTransportDispatcher(self, transportDispatcher, recvId=None):
        self.snmp_engine.registerTransportDispatcher(transportDispatcher,
                                                     recvId)

    def create_managed_object_instance(self):

        module_name = "Unity-MIB"
        instances = []
        table_rows = []

        mib_symbols = [item[0] for item in get_mib_symbols(module_name)]
        # mib_symbols.insert(0, "Unity-MIB")

        mib_objects = self.mib_builder.importSymbols(module_name, *mib_symbols)

        for item in mib_objects:
            if isinstance(item, self.MibTableRow):
                table_rows.append(item)

        for item in mib_objects:
            # class_name = item.label.upper()[:1] + item.label[1:]
            class_name = item.label
            try:
             mod = __import__("unityImpl."+class_name, fromlist=[item.label])
            except ImportError:
                continue

            if isinstance(item, self.MibTableColumn):
                entry = None
                for row in table_rows:
                    if row.getName() == item.getName()[:-1]:
                        entry = row

                scalar_instance_class = factory.ScalarInstanceFactory.build(
                    class_name,
                    base_class=self.MibScalarInstance,
                    impl_class=getattr(mod, class_name)
                )

                column_instance_class = factory.TableColumnInstanceFactory.build(
                    class_name, base_class=self.MibTableColumn,
                    proto_inst=scalar_instance_class,
                    entry=entry,
                )
                instances.append(column_instance_class(item.name, v2c.OctetString()))
            elif isinstance(item, self.MibScalar):
                scalar_instance_class = factory.ScalarInstanceFactory.build(
                    class_name, base_class=self.MibScalarInstance,
                    impl_class=getattr(mod, class_name)
                )
                instances.append(scalar_instance_class(item.name, (0,), v2c.OctetString()))

        # (
        #     agentVersion,
        #     mibVersion,
        #     enclosureTable,
        #     enclosureEntry,
        #     enclosureModel,
        #     enclosureSerialNumber,
        # ) = self.mib_builder.importSymbols(
        #     'Unity-MIB',
        #     'agentVersion',
        #     'mibVersion',
        #     'enclosureTable',
        #     'enclosureEntry',
        #     'enclosureModel',
        #     'enclosureSerialNumber',
        # )
        #
        # AgentVersionScalarInstance = factory.ScalarInstanceFactory.build(
        #     agentVersion.label, base_class=self.MibScalarInstance,
        #     impl_class=AgentInfo,
        #     get_value="get_agent_version",
        # )
        #
        # MibVersionScalarInstance = factory.ScalarInstanceFactory.build(
        #     mibVersion.label, base_class=self.MibScalarInstance,
        #     impl_class=AgentInfo,
        #     get_value="get_mib_version",
        # )
        #
        # EnclosureModelScalarInstance = factory.ScalarInstanceFactory.build(
        #     enclosureModel.label, base_class=self.MibScalarInstance,
        #     impl_class=EnclosureTableInfo,
        #     get_value="get_enclosure_model",
        # )
        #
        # EnclosureSerialNumberScalarInstance = factory.ScalarInstanceFactory.build(
        #     enclosureSerialNumber.label, base_class=self.MibScalarInstance,
        #     impl_class=EnclosureTableInfo,
        #     get_value="get_enclosure_serial_number",
        # )
        #
        # enclosure_names = ['c1', 'c2', 'c3']
        #
        # EnclosureModelColumnInstance = factory.TableColumnInstanceFactory.build(
        #     enclosureModel.label, base_class=self.MibTableColumn,
        #     proto_inst=EnclosureModelScalarInstance,
        #     row_list=enclosure_names,
        #     entry=enclosureEntry,
        # )
        #
        # EnclosureSerialNumberColumnInstance = factory.TableColumnInstanceFactory.build(
        #     enclosureSerialNumber.label, base_class=self.MibTableColumn,
        #     proto_inst=EnclosureSerialNumberScalarInstance,
        #     row_list=enclosure_names,
        #     entry=enclosureEntry,
        # )
        #
        # agentVersionScalarInstance = AgentVersionScalarInstance(agentVersion.name, (0,), v2c.OctetString())
        # mibVersionScalarInstance = MibVersionScalarInstance(mibVersion.name, (0,), v2c.OctetString())
        #
        # enclosureModelColumnInstance = EnclosureModelColumnInstance(enclosureModel.name, v2c.OctetString())
        # enclosureSerialNumberColumnInstance = EnclosureSerialNumberColumnInstance(enclosureSerialNumber.name,
        #                                                                           v2c.OctetString())

        # self.mib_builder.exportSymbols(
        #     'Unity-MIB',
        #     agentVersionScalarInstance,
        #     mibVersionScalarInstance,
        #     enclosureModelColumnInstance,
        #     enclosureSerialNumberColumnInstance,
        # )

        self.mib_builder.exportSymbols('Unity-MIB', *instances)

    def register_snmp_application(self):

        snmp_context = context.SnmpContext(self.snmp_engine)

        # Register SNMP Applications at the SNMP engine for particular SNMP context
        cmdrsp.GetCommandResponder(self.snmp_engine, snmp_context)
        cmdrsp.SetCommandResponder(self.snmp_engine, snmp_context)
        cmdrsp.NextCommandResponder(self.snmp_engine, snmp_context)
        cmdrsp.BulkCommandResponder(self.snmp_engine, snmp_context)

        # Register an imaginary never-ending job to keep I/O dispatcher running forever
        self.snmp_engine.transportDispatcher.jobStarted(1)

    def run(self):

        # Run I/O dispatcher which would receive queries and send responses
        try:
            self.snmp_engine.transportDispatcher.runDispatcher()
        except:
            self.snmp_engine.transportDispatcher.closeDispatcher()
            raise


if __name__ == "__main__":
    engine = SNMPEngine()

    engine.addTransport('0.0.0.0', 161)

    # SNMPv3/USM setup
    # user: usr-md5-des, auth: MD5, priv DES
    # snmpwalk -v3 -u usr-md5-des -l authPriv -A authkey1 -X privkey1 10.32.179.148 .1.3.6
    # snmpget -v3 -u usr-md5-des -l authPriv -A authkey1 -X privkey1 10.32.179.148 .1.3.6.1.4.1.1139.103.2.1.0
    # snmpget -v3 -u usr-md5-des -l authPriv -A authkey1 -X privkey1 10.32.179.148 .1.3.6.1.4.1.1139.103.2.1.0

    user_name = 'usr-md5-des'
    security_level = 'authPriv'
    auth_key = 'authkey1'
    priv_key = 'privkey1'
    read_sub_tree = (1, 3, 6, 1, 4, 1, 1139, 103, 2)

    engine.addVacmUser(3, user_name, security_level, read_sub_tree)

    engine.addV3User(user_name, config.usmHMACMD5AuthProtocol, auth_key,
                     config.usmDESPrivProtocol, priv_key)

    # snmpget -v2c -c public 192.168.56.1 1.3.6.1.4.1.1139.103.2.1.0
    engine.addV1System(user_name, 'public')
    engine.addVacmUser(2, user_name, 'noAuthNoPriv', read_sub_tree)

    engine.create_managed_object_instance()

    engine.register_snmp_application()

    engine.run()
