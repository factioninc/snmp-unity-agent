from snmpagent_unity.commands import user, community, crypto, service

CMD = [user.AddUser, user.UpdateUser, user.DeleteUser, user.ListUsers,
       community.CreateCommunity, community.DeleteCommunity,
       crypto.Encrypt, crypto.Decrypt,
       service.Start, service.Stop, service.Restart, service.Run]

CMD_DICT = {cmd.name: cmd for cmd in CMD}
