# Platform Core v2.24.0 R1 — Install, Validate & Resume Promotion

Use the repaired R1 bundle after the original v2.24.0 promotion stopped on the inherited federation placeholder false positive.

```bash
cd ~/Downloads
chmod +x repair_and_resume_platform_core_v2_24_0_r1_macos.sh
./repair_and_resume_platform_core_v2_24_0_r1_macos.sh \
  sustainable-catalyst-platform-core-v2.24.0-release-bundle-REPAIRED-R1.zip
```

The wrapper verifies bundle checksums, the canonical v2.24.0 contract, the R1 repair contract, the push-safe secret scan, and shell syntax before resuming through the normal v2.24.0 deploy/validate/push script.

Runtime version remains `2.24.0`; migration head remains `0027`.
