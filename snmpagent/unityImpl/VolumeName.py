class VolumeName(object):
    def read_get(self, name, idx_name, unity_client):
        return unity_client.get_lun_name(idx_name)
    # def read_get(self, name, idx, unity_client):
    #     return unity_client.get_lun_name(idx)


class VolumeNameColumn(object):
    def get_idx(self, name, idx, unity_client):
        return unity_client.get_luns()
