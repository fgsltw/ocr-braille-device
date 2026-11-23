// 전체 조립 미리보기 (출력용 아님): 카메라 스탠드 + 문서 자리 + 점자 셀
// 렌더링: openscad -o images/full_assembly.png --imgsize=1600,1100 --viewall --autocenter --camera=0,0,0,60,0,30,1100 full_view.scad
use <braille_cell.scad>
use <camera_stand.scad>

// 카메라 스탠드 (기둥 중심 = 원점, 문서는 앞쪽 -y). 문서 자리(A4 가로) 포함
stand_assembly();

// 점자 셀: 문서 오른쪽, 사용자 쪽(앞)을 -y로
translate([215, -150, 0]) cell_assembly();
