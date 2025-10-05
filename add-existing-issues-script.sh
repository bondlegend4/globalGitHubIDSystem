#!/bin/bash

# Add all existing issues to their project boards
# Replace PROJECT_NUM with actual numbers from your GitHub

# Configuration - UPDATE THESE!
OWNER="bondlegend4"

# Project numbers (find at: https://github.com/users/bondlegend4/projects/)
MODELICA_CORE_PROJECT=5  # UPDATE
FFI_PROJECT=6            # UPDATE
MODBUS_PROJECT=8         # UPDATE
GODOT_PROJECT=11          # UPDATE
COLONY_SIM_PROJECT=7     # UPDATE
LUNACO_PROJECT=9         # UPDATE
VICS_LE_PROJECT=4        # UPDATE
VICS_PROJECT=12           # UPDATE
VICS_SEC_PROJECT=10       # UPDATE

echo "Adding existing issues to project boards..."
echo ""

# Function to add issues from a repo to a project
add_issues_to_project() {
    local repo=$1
    local project_num=$2
    local project_name=$3
    
    echo "Processing: $repo → Project #$project_num ($project_name)"
    
    issue_numbers=$(gh issue list -R "$OWNER/$repo" --json number --jq '.[].number' 2>/dev/null)
    
    if [ -z "$issue_numbers" ]; then
        echo "  No issues found in $repo"
        return
    fi
    
    count=0
    while IFS= read -r issue_num; do
        if [ -n "$issue_num" ]; then
            echo "  Adding issue #$issue_num..."
            gh project item-add "$project_num" \
                --owner "$OWNER" \
                --url "https://github.com/$OWNER/$repo/issues/$issue_num" 2>/dev/null
            ((count++))
        fi
    done <<< "$issue_numbers"
    
    echo "  ✓ Added $count issues from $repo"
    echo ""
}

# Add issues from each repo to its own project
echo "Adding issues from repos to their own project"
add_issues_to_project "space-colony-modelica-core" "$MODELICA_CORE_PROJECT" "Modelica Core"
add_issues_to_project "modelica-rust-ffi" "$FFI_PROJECT" "FFI"
add_issues_to_project "modelica-rust-modbus-server" "$MODBUS_PROJECT" "Modbus Server"
add_issues_to_project "godot-modelica-rust-integration" "$GODOT_PROJECT" "Godot Integration"
add_issues_to_project "lunaco-sim" "$LUNACO_PROJECT" "LunaCo Sim"
add_issues_to_project "V-ICS" "$VICS_SEC_PROJECT" "VICS Security"

# Adding issues 
echo "Adding issues from repos to the v-ics.le project"
add_issues_to_project "space-colony-modelica-core" "$VICS_LE_PROJECT" "v-ics.le (parent)"
add_issues_to_project "modelica-rust-ffi" "$VICS_LE_PROJECT" "v-ics.le (parent)"
add_issues_to_project "modelica-rust-modbus-server" "$VICS_LE_PROJECT" "v-ics.le (parent)"
add_issues_to_project "godot-modelica-rust-integration" "$VICS_LE_PROJECT" "v-ics.le (parent)"
add_issues_to_project "lunaco-sim" "$VICS_LE_PROJECT" "v-ics.le (parent)"
add_issues_to_project "V-ICS" "$VICS_LE_PROJECT" "v-ics.le (parent)"

# Add Godot Integration issues to Colony Sim parent project
echo "Adding Godot Integration issues to Colony Sim parent..."
add_issues_to_project "godot-modelica-rust-integration" "$COLONY_SIM_PROJECT" "Colony Sim (parent)"
add_issues_to_project "modelica-rust-ffi" "$COLONY_SIM_PROJECT" "Colony Sim (parent)"
add_issues_to_project "space-colony-modelica-core" "$COLONY_SIM_PROJECT" "Colony Sim (parent)"

# Add Modbus Integration issues to V-ICS parent project
echo "Adding Modbus Integration issues to V-ICS parent..."
add_issues_to_project "space-colony-modelica-core" "$VICS_PROJECT" "V-ICS (modbus)"
add_issues_to_project "modelica-rust-ffi" "$VICS_PROJECT" "V-ICS (modbus)"
add_issues_to_project "modelica-rust-modbus-server" "$VICS_PROJECT" "V-ICS (modbus)"
add_issues_to_project "V-ICS" "$VICS_PROJECT" "V-ICS (security)"

# Add Modelica Rust FII issues to rust integrations parent project
add_issues_to_project "modelica-rust-ffi" "$GODOT_PROJECT" "Godot Integration"
add_issues_to_project "modelica-rust-ffi" "$MODBUS_PROJECT" "Modbus Server"


echo "Done! Check your project boards."
