class VolumeHostInfo(object):
    def read_get(self, name, idx_name, unity_client):
        return unity_client.get_lun_host_access(idx_name)


class VolumeHostInfoColumn(object):
    def get_idx(self, name, idx, unity_client):
        return unity_client.get_luns()
