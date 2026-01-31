from typing import List

class DatasetRepository:
    def __init__(self):
        pass

    def create_config_template(self, template) -> id:
        pass

    def get_config_template(self, template_id) -> dict:
        pass

    def is_config_available(self, config_hash) -> int:
        pass

    def get_new_template_version_number(self):
        pass

    def create_run(self, template_id, note="") -> int:
        pass

    def get_run_samples(self, run_id) -> List[dict]:
        pass