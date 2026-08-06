$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$venv = "D:\CodexDeps\lora_training\venv\Scripts"
$scripts = "D:\CodexDeps\sd-scripts"
$ckpt = "D:\CodexDeps\stable-diffusion-webui\models\Stable-diffusion\sd_xl_base_1.0.safetensors"
$data = "D:\CodexDeps\lora_training\dataset_bramble"
$out = "D:\CodexDeps\lora_training\output_lu_bramble_clerk_candidate"
$log = "D:\CodexDeps\lora_training\train_lu_bramble_clerk_candidate.log"

if (-not (Test-Path -LiteralPath "$venv\accelerate.exe")) { throw "Missing accelerate.exe: $venv\accelerate.exe" }
if (-not (Test-Path -LiteralPath "$scripts\sdxl_train_network.py")) { throw "Missing sd-scripts trainer: $scripts\sdxl_train_network.py" }
if (-not (Test-Path -LiteralPath $ckpt)) { throw "Missing checkpoint: $ckpt" }
if (-not (Test-Path -LiteralPath $data)) { throw "Missing staged dataset: $data" }

New-Item -ItemType Directory -Force -Path $out | Out-Null

Push-Location $scripts
try {
  $ErrorActionPreference = "Continue"
  & "$venv\accelerate.exe" launch `
    --mixed_precision=bf16 `
    --num_processes=1 `
    --num_machines=1 `
    --num_cpu_threads_per_process=4 `
    sdxl_train_network.py `
    --pretrained_model_name_or_path="$ckpt" `
    --train_data_dir="$data" `
    --output_dir="$out" `
    --output_name="lu_bramble_clerk_candidate" `
    --resolution="1024,1024" `
    --network_module=networks.lora `
    --network_dim=32 `
    --network_alpha=16 `
    --learning_rate=1.5e-4 `
    --text_encoder_lr=5e-5 `
    --unet_lr=1.5e-4 `
    --optimizer_type=AdamW8bit `
    --train_batch_size=1 `
    --gradient_checkpointing `
    --gradient_accumulation_steps=1 `
    --max_train_steps=48 `
    --save_every_n_steps=24 `
    --save_model_as=safetensors `
    --mixed_precision=bf16 `
    --caption_extension=".txt" `
    --cache_latents `
    --cache_latents_to_disk `
    --seed=41004 `
    --logging_dir="$out\logs" 2>&1 | Tee-Object -FilePath $log
  $exitCode = $LASTEXITCODE
  $ErrorActionPreference = "Stop"
  if ($exitCode -ne 0) {
    throw "Bramble candidate LoRA training failed with exit code $exitCode. See $log"
  }
}
finally {
  Pop-Location
}
