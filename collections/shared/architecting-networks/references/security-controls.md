# Security Controls

## Security Groups vs Network ACLs

### Security Groups (Recommended)

**Characteristics:**
- Stateful (return traffic allowed automatically)
- Instance-level control
- Allow rules only (implicit deny)
- Can reference other security groups

**Best Practices:**
- Descriptive names
- Reference other SGs instead of CIDR blocks
- Minimal, specific rules
- One security group per service

### Network ACLs

**Characteristics:**
- Stateless (must allow both request and response)
- Subnet-level control
- Allow and deny rules
- Rules processed in order

**When to Use:**
- Explicit deny rules (block specific IPs)
- Compliance requirements
- Extra layer beyond security groups

**Important:**
- Account for ephemeral ports (1024-65535)
- Test thoroughly (statelessness causes issues)

## Decision Matrix

| Requirement | Security Group | Network ACL |
|-------------|----------------|-------------|
| Block specific IP | No | Yes (deny rule) |
| Instance-level control | Yes | No |
| Stateful filtering | Yes | No |
| Reference other SGs | Yes | No |
| Default recommendation | Yes | Only if needed |
