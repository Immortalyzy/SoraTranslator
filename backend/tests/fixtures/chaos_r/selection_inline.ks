[macro name='setup']
*scene_start
[cm]
*SEL01|Label A/Label B
[sel1 text='First choice' target=*SEL01_1]
[sel2 text="Second choice" target=*SEL01_2]
*SEL01_1
[jump storage='scene.ks' target='route_a']
*SEL01_2
[【Alice】]Route two line[nl]
*main
Narration line[nl]
