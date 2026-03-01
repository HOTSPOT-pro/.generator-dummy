import csv
import os
from config.db_config import OUTPUT_DIR

class CSVWriterManager:

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        self.files = {
            'member': self._open('member.csv'),
            'social_account': self._open('social_account.csv'),
            'subscription': self._open('subscription.csv'),
            'notification_allow': self._open('notification_allow.csv'),
            'family': self._open('family.csv'),
            'family_sub': self._open('family_sub.csv'),
            'family_apply': self._open('family_apply.csv'),
            'family_apply_target': self._open('family_apply_target.csv'),
            'block_policy': self._open('block_policy.csv'),
            'policy_sub': self._open('policy_sub.csv'),
            'blocked_service_sub': self._open('blocked_service_sub.csv'),
            'present_data': self._open('present_data.csv'),
            'notification': self._open('notification.csv'),
        }

        self.writers = {k: csv.writer(v) for k, v in self.files.items()}

    def _open(self, filename):
        return open(
            os.path.join(OUTPUT_DIR, filename),
            'w',
            newline='',
            encoding='utf-8',
            buffering=1024*1024
        )

    def writer(self, name):
        return self.writers[name]

    def close(self):
        for f in self.files.values():
            f.close()
