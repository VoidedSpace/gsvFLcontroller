import mido

print(mido.get_output_names())
print(mido.get_input_names())



toFL = mido.open_output(name='loopMIDI Port 10', virtual = False)
fromFL = mido.open_input(name='loopMIDI Port 1 10')

while (1):

    msg = fromFL.poll()




    if (msg):
        print(msg)
