---
name: terraform-basics
description: >
  Terraform fundamentals — HCL basics, resource/module structure, state
  management, plan/apply workflow, provider configuration, and common patterns.
  Use this skill when provisioning cloud infrastructure as code, reviewing
  Terraform configs, or setting up a new Terraform project.
category: devops
tags: [terraform, iac, infrastructure, cloud, devops]
related: [docker-basics, github-actions]
---

# Terraform Basics

> Infrastructure as code means your infra is version-controlled, reviewable, and repeatable. Terraform is the lingua franca for this.

## When to Use This Skill

- Provisioning cloud resources (AWS, GCP, Azure) with code
- Setting up a new Terraform project structure
- Reviewing Terraform plans for safety
- Understanding state management and remote backends
- Debugging "plan says no changes but infra is different"

---

## Core Concepts

| Concept | What it is |
|---------|------------|
| **Provider** | Plugin that talks to an API (AWS, GCP, GitHub, etc.) |
| **Resource** | One piece of infrastructure (`aws_s3_bucket`, `google_compute_instance`) |
| **Data source** | Read-only lookup of existing infra |
| **Module** | Reusable group of resources |
| **State** | Terraform's record of what it manages |
| **Plan** | Preview of changes before applying |
| **Apply** | Execute the plan and make changes |

---

## Project Structure

```
infra/
├── main.tf            # provider config, top-level resources
├── variables.tf       # input variables
├── outputs.tf         # output values
├── terraform.tfvars   # variable values (gitignored if contains secrets)
├── backend.tf         # remote state config
├── versions.tf        # required providers + terraform version
└── modules/
    └── vpc/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Rules

1. **One environment per directory or workspace.** Don't mix prod and staging in the same state.
2. **Pin provider versions.**
   ```hcl
   terraform {
     required_providers {
       aws = {
         source  = "hashicorp/aws"
         version = "~> 5.0"
       }
     }
     required_version = ">= 1.7"
   }
   ```
3. **Pin module versions.** `source = "git::https://...?ref=v1.2.0"`.

---

## The Plan/Apply Workflow

```bash
terraform init       # download providers, init backend
terraform plan       # preview changes (read-only)
terraform apply      # make changes (requires confirmation)
terraform destroy    # tear down (DANGEROUS)
```

4. **Always `plan` before `apply`.** Read the plan carefully. Especially look for `destroy` lines.
5. **In CI, use `terraform plan -out=plan.tfplan` then `terraform apply plan.tfplan`.** Ensures the exact reviewed plan is applied.
6. **Never `terraform apply` without reviewing the plan.**

---

## State Management

Terraform state is the mapping between your `.tf` files and real infrastructure.

### Remote Backend (required for teams)

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

7. **Always use remote state** (S3, GCS, Terraform Cloud). Local state = team conflicts.
8. **Enable state locking** (DynamoDB for S3, native for GCS/TF Cloud). Prevents concurrent applies.
9. **Encrypt state at rest.** State contains sensitive values (passwords, keys).
10. **Never edit state by hand.** Use `terraform state mv`, `terraform state rm`, `terraform import`.

---

## Variables & Outputs

### Variables

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "db_password" {
  type      = string
  sensitive = true
}
```

11. **Every variable has `description` and `type`.** Self-documenting.
12. **Mark sensitive variables.** `sensitive = true` redacts from plan output.
13. **Use `validation` blocks** for constraints.
14. **Don't commit `terraform.tfvars` if it contains secrets.** Use environment variables: `TF_VAR_db_password`.

### Outputs

```hcl
output "api_url" {
  value       = aws_api_gateway_stage.main.invoke_url
  description = "API Gateway URL"
}
```

Outputs are how modules expose values to callers and how `terraform output` works.

---

## Modules

### When to create a module

- Same pattern used in 2+ places
- Logical grouping of resources (VPC + subnets + routing)
- Team wants to enforce standards

### Module interface

```hcl
module "vpc" {
  source = "./modules/vpc"

  cidr_block  = "10.0.0.0/16"
  environment = var.environment
}
```

15. **Modules have a clear interface** (`variables.tf` = inputs, `outputs.tf` = outputs).
16. **Don't nest modules deeply.** One level of nesting is usually enough.
17. **Pin module source versions.**

---

## Common Patterns

### Tagging

```hcl
locals {
  common_tags = {
    Project     = "my-app"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket" "main" {
  bucket = "my-app-${var.environment}"
  tags   = local.common_tags
}
```

18. **Tag everything with `ManagedBy = terraform`.** Humans and scripts can distinguish TF-managed resources.

### Count vs for_each

- **`count`** for simple on/off or numeric repetition
- **`for_each`** for maps/sets (preferred — doesn't reindex on removal)

```hcl
resource "aws_iam_user" "users" {
  for_each = toset(["alice", "bob", "charlie"])
  name     = each.value
}
```

19. **Prefer `for_each` over `count`.** Removing an item from a `count` list shifts all indices.

---

## Safety

20. **Use `prevent_destroy` for critical resources.**
    ```hcl
    resource "aws_rds_instance" "main" {
      lifecycle { prevent_destroy = true }
    }
    ```

21. **Review `destroy` lines in plan carefully.** Renaming a resource = destroy + create.
22. **Use `moved` blocks for refactoring** instead of destroy + recreate.
    ```hcl
    moved {
      from = aws_s3_bucket.old_name
      to   = aws_s3_bucket.new_name
    }
    ```

23. **Never run `terraform destroy` on production without peer review.**

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Local state for team projects | Remote backend with locking |
| Hardcoded values | Variables with defaults |
| No provider version pinning | `version = "~> 5.0"` |
| Editing state files by hand | `terraform state` commands |
| One state file for everything | Split by environment and concern |
| `terraform apply -auto-approve` in prod | Always review plan |
| Secrets in `.tf` files or `.tfvars` committed to git | Environment variables or secret manager |
| Copy-pasting resource blocks | Create a module |

---

## Checklist

- [ ] Provider and Terraform versions pinned
- [ ] Remote backend with state locking enabled
- [ ] State encrypted at rest
- [ ] Every variable has type and description
- [ ] Sensitive variables marked
- [ ] Resources tagged with `ManagedBy = terraform`
- [ ] Critical resources have `prevent_destroy`
- [ ] CI runs `terraform plan` on PRs
- [ ] `terraform apply` requires human review (no auto-approve in prod)
- [ ] Modules used for repeated patterns

---

## Related Skills

- [`docker-basics`](../docker-basics/SKILL.md) — containerize; Terraform provisions the infra it runs on
- [`github-actions`](../github-actions/SKILL.md) — run Terraform in CI
