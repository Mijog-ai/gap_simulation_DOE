import sys

def scale_z(input_file):
    # Read the configuration file
    with open(input_file, 'r') as f:
        lines = f.readlines()

    original_inp = lines[0].strip()
    new_inp = lines[1].strip()
    z1, z1new = map(float, lines[2].strip().split())
    z2, z2new = map(float, lines[3].strip().split())

    # Read the original Abaqus input file
    with open(original_inp, 'r') as f:
        original_lines = f.readlines()

    # Write to the new scaled Abaqus input file
    with open(new_inp, 'w') as f:
        in_node_section = False
        for line in original_lines:
            stripped_line = line.strip()
            if stripped_line.startswith('*NODE'):
                f.write(line)
                in_node_section = True
                continue
            if in_node_section and stripped_line.startswith('*'):
                in_node_section = False
            if in_node_section and stripped_line:
                # Parse node line: assuming format "node_id, x, y, z"
                parts = [p.strip() for p in stripped_line.split(',')]
                if len(parts) != 4:
                    # If not a valid node line, write it unchanged
                    f.write(line)
                    continue
                node_id = parts[0]
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])
                except ValueError:
                    # If parsing fails, write original line
                    f.write(line)
                    continue

                # Scale Z-coordinate
                if z <= z1:
                    new_z = z  # No change for Z <= Z1
                elif z <= z2:
                    if z2 - z1 == 0:
                        new_z = z1new  # Avoid division by zero
                    else:
                        # Linear interpolation: new_z = z1new + (z - z1) * (z2new - z1new) / (z2 - z1)
                        new_z = z1new + (z - z1) * (z2new - z1new) / (z2 - z1)
                else:
                    # Apply offset for Z > Z2
                    new_z = z + (z2new - z2)

                # Write the scaled node with formatting similar to Abaqus style
                f.write(f"{node_id:10}, {x:20.13E}, {y:20.13E}, {new_z:20.13E}\n")
                continue
            f.write(line)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python z_scaler.py <input_config_file>")
        sys.exit(1)
    scale_z(sys.argv[1])
