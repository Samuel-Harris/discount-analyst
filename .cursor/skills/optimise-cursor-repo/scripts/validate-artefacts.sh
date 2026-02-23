#!/bin/bash
# Validate Cursor artefact frontmatter (skills, rules, subagents)
# Run from the project root directory

set -uo pipefail

RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

errors=0
warnings=0
info=0

# Extract frontmatter from a file (content between first and second ---)
extract_frontmatter() {
    local file="$1"
    awk '/^---$/ { if (++count == 2) exit } count == 1 { print }' "$file"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

print_error() {
    echo -e "  ${RED}ERROR:${NC} $1"
    ((errors++))
}

print_warning() {
    echo -e "  ${YELLOW}WARNING:${NC} $1"
    ((warnings++))
}

print_info() {
    echo -e "  ${BLUE}INFO:${NC} $1"
    ((info++))
}

print_ok() {
    echo -e "  ${GREEN}OK${NC}"
}

# Validate Skills
validate_skills() {
    print_header "Validating Skills (.cursor/skills/**/SKILL.md)"

    skill_count=$(find .cursor/skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

    if [ "$skill_count" -eq 0 ]; then
        echo "  No skills found"
        return
    fi

    while IFS= read -r skill; do
        echo -e "\n  Checking ${skill}..."
        has_issues=false

        if ! head -1 "$skill" | grep -q "^---$"; then
            print_error "Missing frontmatter (no opening ---)"
            has_issues=true
        else
            frontmatter=$(extract_frontmatter "$skill")

            if ! echo "$frontmatter" | grep -q "^name:"; then
                print_error "Missing 'name' field"
                has_issues=true
            fi

            if ! echo "$frontmatter" | grep -q "^description:"; then
                print_error "Missing 'description' field (agent won't discover this skill)"
                has_issues=true
            fi
        fi

        if [ "$has_issues" = false ]; then
            print_ok
        fi
    done < <(find .cursor/skills -name "SKILL.md" 2>/dev/null | sort)
}

# Validate Rules
validate_rules() {
    print_header "Validating Rules (.cursor/rules/*.mdc)"

    if ! compgen -G ".cursor/rules/*.mdc" > /dev/null 2>&1; then
        echo "  No rules found"
        return
    fi

    for rule in .cursor/rules/*.mdc; do
        echo -e "\n  Checking ${rule}..."
        has_issues=false

        if ! head -1 "$rule" | grep -q "^---$"; then
            print_error "Missing frontmatter"
            has_issues=true
        else
            frontmatter=$(extract_frontmatter "$rule")
            has_always=$(echo "$frontmatter" | grep -c "^alwaysApply: true" || true)
            has_globs=$(echo "$frontmatter" | grep -c "^globs:" || true)
            has_desc=$(echo "$frontmatter" | grep -c "^description:" || true)
            globs_empty=$(echo "$frontmatter" | grep -c "^globs:$\|^globs: \[\]$" || true)

            if [ "$has_always" -gt 0 ] && [ "$has_globs" -gt 0 ]; then
                print_warning "Has both alwaysApply: true AND globs (globs are ignored)"
                has_issues=true
            fi

            if [ "$has_globs" -gt 0 ] && [ "$globs_empty" -gt 0 ]; then
                print_error "globs field is empty"
                has_issues=true
            fi

            if [ "$has_desc" -gt 0 ] && [ "$has_globs" -eq 0 ] && [ "$has_always" -eq 0 ]; then
                print_info "Apply Intelligently rule (consider skill migration if procedural)"
                has_issues=true
            fi
        fi

        if [ "$has_issues" = false ]; then
            print_ok
        fi
    done
}

# Validate Subagents
validate_subagents() {
    print_header "Validating Subagents (.cursor/agents/*.md)"

    if ! compgen -G ".cursor/agents/*.md" > /dev/null 2>&1; then
        echo "  No subagents found"
        return
    fi

    for agent in .cursor/agents/*.md; do
        echo -e "\n  Checking ${agent}..."
        has_issues=false

        if ! head -1 "$agent" | grep -q "^---$"; then
            print_warning "No frontmatter (subagent will use filename as name)"
            has_issues=true
        else
            frontmatter=$(extract_frontmatter "$agent")

            if ! echo "$frontmatter" | grep -q "^description:"; then
                print_warning "Missing 'description' field (agent won't auto-delegate to this subagent)"
                has_issues=true
            fi

            model_line=$(echo "$frontmatter" | grep "^model:" || true)
            if [ -n "$model_line" ]; then
                model_value=$(echo "$model_line" | sed 's/^model: *//')
                case "$model_value" in
                    fast|inherit|"") ;;
                    *) print_info "model '$model_value' - ensure this is a valid model ID"
                       has_issues=true ;;
                esac
            fi
        fi

        if [ "$has_issues" = false ]; then
            print_ok
        fi
    done
}

# Summary
print_summary() {
    echo -e "\n${BLUE}=== Summary ===${NC}"
    echo -e "  Errors:   ${RED}${errors}${NC}"
    echo -e "  Warnings: ${YELLOW}${warnings}${NC}"
    echo -e "  Info:     ${BLUE}${info}${NC}"

    if [ "$errors" -gt 0 ]; then
        exit 1
    fi
}

# Main
echo "Cursor Artefact Validator"
echo "========================="

validate_skills
validate_rules
validate_subagents
print_summary
