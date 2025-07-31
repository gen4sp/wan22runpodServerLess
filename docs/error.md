    import torchvision

File "/opt/venv/lib/python3.12/site-packages/torchvision/**init**.py", line 10, in <module>
from torchvision import \_meta_registrations, datasets, io, models, ops, transforms, utils # usort:skip
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/opt/venv/lib/python3.12/site-packages/torchvision/\_meta_registrations.py", line 163, in <module>
@torch.library.register_fake("torchvision::nms")
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/opt/venv/lib/python3.12/site-packages/torch/library.py", line 1023, in register
use_lib.\_register_fake(op_name, func, \_stacklevel=stacklevel + 1)
File "/opt/venv/lib/python3.12/site-packages/torch/library.py", line 214, in \_register_fake
handle = entry.fake_impl.register(func_to_register, source)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/opt/venv/lib/python3.12/site-packages/torch/\_library/fake_impl.py", line 31, in register
if torch.\_C.\_dispatch_has_kernel_for_dispatch_key(self.qualname, "Meta"):
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: operator torchvision::nms does not exist
worker-comfyui - Starting handler...
--- Starting Serverless Worker | Version 1.7.13 ---
{"requestId": null, "message": "Jobs in queue: 1", "level": "INFO"}
{"requestId": null, "message": "Jobs in progress: 1", "level": "INFO"}
{"requestId": "11d4c7ad-ac0d-4266-9d5f-9cae50dde9fa-u2", "message": "Started.", "level": "INFO"}
worker-comfyui - Checking API server at http://127.0.0.1:8188/...
worker-comfyui - Failed to connect to server at http://127.0.0.1:8188/ after 500 attempts.
{"requestId": "11d4c7ad-ac0d-4266-9d5f-9cae50dde9fa-u2", "message": "Finished.", "level": "INFO"}
