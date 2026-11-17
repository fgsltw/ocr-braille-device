// 촉각 점자 셀 (확대 셀) — SG90 서보 6개 + 3D 프린트 부품
//
// 구조: 서보 6개를 셀 주위에 원형으로 세우고, 각 서보의 레버가 자기 점 방향에서
// 들어와 핀 아래 턱(플랜지)을 밀어 올린다. 플랜지가 뚜껑 아래 돌기부(boss)에 닿는
// 높이 = 돌기 최대 높이 (기구로 고정). 레버 끝이 얇아 살짝 휘므로 서보가 조금 더
// 돌아도 무리가 없고, 그 탄성으로 돌기를 단단히 받친다.
//
// 내보내기 (저장소 루트에서):  bash hardware/export_stl.sh
// 한 부품만:  openscad -D 'part="lid"' -o lid.stl hardware/braille_cell.scad
//
// 부품 (괄호 = 출력 개수)
//   base(1)  servo_mount(6)  lever_a(4: 점 1·3·4·6)  lever_b(2: 점 2·5)
//   pin(6+여분)  lid(1)  fit_test(1, 가장 먼저 출력해 핀 구멍 여유 확인)
//   assembly = 조립 미리보기 (출력용 아님)

part = "assembly";

/* [점자 셀] */
dot_pitch  = 6;     // 점 간격 (확대 셀). 표준 셀은 약 2.5지만 이 구조로는 어렵다
pin_d      = 3;     // 핀 지름
pin_clear  = 0.3;   // 핀 구멍 여유 — fit_test로 고른 값으로 바꾼다
flange_d   = 5;     // 핀 아래 턱 지름 (dot_pitch보다 작아야 함)
flange_h   = 1.5;
lift       = 1.0;   // 돌기 높이 (뚜껑 윗면 위로 올라오는 양)
dome_h     = 0.6;   // 핀 끝 둥글기

/* [SG90 치수 — 가진 서보를 재서 맞춘다] */
servo_L    = 22.2;  // 몸체 길이 (탭 방향) — 구매처 표기 31×22.2×11.8mm
servo_W    = 11.8;  // 몸체 폭 — 구매처 표기
servo_H    = 22.5;  // 몸체 높이 (축 방향, 기어 돌출부 제외)
shaft_from_end = 5.9;   // 축 중심 ~ 가까운 몸체 끝
tab_span   = 32.2;  // 탭 포함 전체 길이
tab_t      = 2.5;   // 탭 두께
tab_top    = 15.9;  // 몸체 바닥 ~ 탭 윗면
hole_spacing = 27.8;    // 탭 나사 구멍 간격
horn_face  = 5.5;   // 몸체 윗면 ~ 혼 팔 바깥면 (혼을 끼운 상태로 잰다)
horn_hub_d = 7.0;   // 혼 허브 지름
horn_len   = 15;    // 축 중심 ~ 혼 팔 끝 둥근 부분 중심 (외팔 혼)
horn_w_hub = 6;     // 혼 팔 폭 (허브 쪽)
horn_w_tip = 4;     // 혼 팔 폭 (끝 쪽)
horn_t     = 1.6;   // 혼 팔 두께
bump_h     = 4.0;   // 몸체 윗면 ~ 기어 돌출부 꼭대기

/* [기구] */
R          = 40;    // 셀 중심 ~ 서보 축 거리
z_shaft    = 26;    // 바닥 ~ 서보 축 높이
floor_t    = 3;
wall_t     = 3;
lid_t      = 3;
inner      = 56;    // 상자 안쪽 반폭
lever_t    = 4;     // 레버 두께 (축 방향)
lever_tip_h = 2;    // 레버 휘는 부분 높이 — 작을수록 부드럽게 휜다
lever_hub_r = 7;
clr        = 0.3;   // 일반 끼움 여유
mount_t    = 3;     // 서보 받침판 두께

$fn = 40;

// ── 계산값 ────────────────────────────────────────────
pocket_d   = horn_t + 0.2;
t_body_top = -lever_t/2 - (horn_face - pocket_d);  // 레버 중심면 기준 서보 몸체 윗면 위치
bump_relief = max(0, bump_h + 0.5 - (horn_face - pocket_d));  // 레버 뒷면 파낼 깊이
z_rest     = z_shaft + lever_tip_h/2;   // 레버가 수평일 때 레버 윗면 = 플랜지 바닥
z_stop     = z_rest + flange_h;         // 돌기부 아랫면 (플랜지가 닿는 곳)
lid_top    = z_shaft + 15;
lid_under  = lid_top - lid_t;
boss_h     = lid_top - z_stop;
pin_len    = boss_h + lift;             // 플랜지 위 핀 길이
outer      = inner + wall_t;
x_floor    = floor_t - z_shaft;         // 서보 좌표계에서 바닥 윗면

// 점 1~6 위치 (위에서 볼 때, 사용자 쪽 = -y. 점 1 = 왼쪽 위)
dots = [[-dot_pitch/2,  dot_pitch], [-dot_pitch/2, 0], [-dot_pitch/2, -dot_pitch],
        [ dot_pitch/2,  dot_pitch], [ dot_pitch/2, 0], [ dot_pitch/2, -dot_pitch]];

function ang(i) = atan2(dots[i][1], dots[i][0]);
function dist(i) = norm(dots[i]);

// 서보 좌표계: 원점 = 축 중심의 몸체 윗면, +Z = 축(레버 쪽), +X = 위(세계 Z), +Y = 바깥(반지름)
module at_servo(i) {
    a = ang(i); c = cos(a); s = sin(a);
    o = [R*c, R*s, z_shaft] + t_body_top * [-s, c, 0];
    multmatrix([[0, c, -s, o[0]], [0, s, c, o[1]], [1, 0, 0, o[2]], [0, 0, 0, 1]]) children();
}

// 레버 좌표계: 원점 = 서보 축, +X = 셀 중심 쪽, +Y = 위, +Z = 축 방향
module at_lever(i) {
    a = ang(i); c = cos(a); s = sin(a);
    multmatrix([[-c, 0, -s, R*c], [-s, 0, c, R*s], [0, 1, 0, z_shaft], [0, 0, 0, 1]]) children();
}

body_x0 = -(servo_L - shaft_from_end);       // 몸체 아래쪽 끝 (서보 좌표 x)
body_cx = body_x0 + servo_L/2;
tab_z1  = -servo_H + tab_top;                // 탭 윗면 (서보 좌표 z)
tab_z0  = tab_z1 - tab_t;
mount_z1 = tab_z0;                           // 받침판 윗면 = 탭 아랫면
mount_z0 = mount_z1 - mount_t;
mount_x1 = (lid_under - z_shaft) - 0.3;      // 받침판 위끝: 뚜껑이 눌러 고정

// ── SG90 모형 (미리보기용) ─────────────────────────────
module sg90() {
    color("royalblue") {
        translate([body_x0, -servo_W/2, -servo_H]) cube([servo_L, servo_W, servo_H]);
        translate([body_x0 - (tab_span - servo_L)/2, -servo_W/2, tab_z0]) cube([tab_span, servo_W, tab_t]);
        cylinder(d = servo_W, h = bump_h);
    }
    color("white") cylinder(d = 4.8, h = horn_face - horn_t);
}

// ── 서보 받침판 (6개) ──────────────────────────────────
module servo_mount() {
    difference() {
        translate([x_floor, -10, mount_z0]) cube([mount_x1 - x_floor, 20, mount_t]);
        translate([body_x0 - clr, -servo_W/2 - clr, mount_z0 - 1])
            cube([servo_L + 2*clr, servo_W + 2*clr, mount_t + 2]);
        for (dx = [-hole_spacing/2, hole_spacing/2])
            translate([body_cx + dx, 0, mount_z0 - 1]) cylinder(d = 1.8, h = mount_t + 2);
    }
}

// 받침판을 바닥에 세우는 홈 (서보 좌표계)
module mount_socket() {
    rail_h = 5;
    // 서보 몸체 쪽(-z) 레일: 전체 폭
    translate([x_floor, -10, mount_z0 - clr - 2]) cube([rail_h, 20, 2]);
    // 탭 쪽(+z) 레일: 아래 탭을 피해 양 끝만
    for (y0 = [-10, servo_W/2 + 1])
        translate([x_floor, y0, mount_z1 + clr]) cube([rail_h, 10 - servo_W/2 - 1, 2]);
}

// ── 레버 (2D 옆모습) ───────────────────────────────────
module lever_2d(L) {
    hull() {
        circle(r = lever_hub_r);
        translate([12, -3]) square([0.1, 6]);
    }
    // 끝은 핀 중심을 0.5mm만 지나게 (더 길면 맞은편 레버와 가운데서 부딪힌다)
    translate([11, -lever_tip_h/2]) square([L + 0.5 - 11, lever_tip_h]);
    translate([L + 0.5, 0]) circle(d = lever_tip_h);
}

module horn_2d(extra) {
    hull() {
        circle(d = horn_hub_d + extra);
        translate([horn_len, 0]) circle(d = horn_w_tip + extra);
        translate([4, -(horn_w_hub + extra)/2]) square([0.1, horn_w_hub + extra]);
    }
}

// 레버: 뒷면(서보 쪽, -z)에 혼 팔이 들어가는 홈, 허브는 관통
module lever(L) {
    difference() {
        translate([0, 0, -lever_t/2]) linear_extrude(lever_t) lever_2d(L);
        translate([0, 0, -lever_t/2 - 1]) linear_extrude(pocket_d + 1) horn_2d(0.4);
        translate([0, 0, -lever_t]) cylinder(d = horn_hub_d + 0.4, h = 2*lever_t);
        // 서보 윗면 기어 돌출부와 닿지 않게 뒷면을 살짝 파낸다
        translate([0, 0, -lever_t/2 - 1]) cylinder(d = servo_W + 1, h = 1 + bump_relief);
    }
}

L_a = R - dist(0);   // 점 1·3·4·6
L_b = R - dist(1);   // 점 2·5

// ── 핀 ────────────────────────────────────────────────
module pin() {
    cylinder(d = flange_d, h = flange_h);
    translate([0, 0, flange_h]) cylinder(d = pin_d, h = pin_len - dome_h);
    translate([0, 0, flange_h + pin_len - dome_h])
        scale([1, 1, dome_h / (pin_d/2)]) sphere(d = pin_d);
}

// ── 상자 (바닥 + 벽 + 받침판 홈) ────────────────────────
module base() {
    difference() {
        translate([-outer, -outer, 0]) cube([2*outer, 2*outer, lid_under]);
        translate([-inner, -inner, floor_t]) cube([2*inner, 2*inner, lid_under]);
        // 뒤쪽(+y) 벽 아래 전선 구멍
        translate([-15, inner - 1, floor_t]) cube([30, wall_t + 2, 12]);
    }
    for (i = [0:5]) at_servo(i) mount_socket();
}

// ── 뚜껑 (손가락 닿는 면, 핀 안내부) ─────────────────────
boss_hx = dot_pitch/2 + flange_d/2 + 1.5;
boss_hy = dot_pitch   + flange_d/2 + 1.5;

module lid() {
    difference() {
        union() {
            translate([-outer, -outer, lid_under]) cube([2*outer, 2*outer, lid_t]);
            // 벽 안쪽에 걸리는 턱
            difference() {
                translate([-inner + clr, -inner + clr, lid_under - 3]) cube([2*(inner - clr), 2*(inner - clr), 3]);
                translate([-inner + clr + 2, -inner + clr + 2, lid_under - 4]) cube([2*(inner - clr - 2), 2*(inner - clr - 2), 5]);
            }
            // 핀 안내 돌기부
            translate([-boss_hx, -boss_hy, z_stop]) cube([2*boss_hx, 2*boss_hy, lid_under - z_stop + 0.01]);
        }
        for (d = dots) translate([d[0], d[1], z_stop - 1]) cylinder(d = pin_d + pin_clear, h = boss_h + 2);
        // 앞쪽 표시 (손으로 방향 확인): 사용자 쪽 가장자리 가운데 홈. 윗면을 평평하게 두어 뒤집어 출력할 수 있게
        translate([-6, -outer + 4, lid_top - 0.8]) cube([12, 2, 1]);
    }
}

// ── 공차 시험판 ───────────────────────────────────────
module fit_test() {
    clears = [0.2, 0.3, 0.4, 0.5];
    difference() {
        cube([10 * len(clears) + 4, 12, 8]);
        for (k = [0:len(clears) - 1]) {
            translate([7 + 10*k, 6, -1]) cylinder(d = pin_d + clears[k], h = 10);
            // 여유값 표시: 홈 개수 = 몇 번째 (1개 = 0.2, 2개 = 0.3 ...)
            for (n = [0:k]) translate([3.5 + 10*k + 2*n, -0.5, 6]) cube([1, 2, 3]);
        }
    }
    translate([10 * len(clears) + 10, 6, 0]) pin();
}

// ── 조립 미리보기 ──────────────────────────────────────
module assembly() {
    color("lightgray") base();
    for (i = [0:5]) {
        at_servo(i) { sg90(); color("orange") servo_mount(); }
        at_lever(i) color("tomato") lever(i == 1 || i == 4 ? L_b : L_a);
        translate([dots[i][0], dots[i][1], z_rest]) color("gold") pin();
    }
    color("lightgreen", 0.35) lid();
}

// ── 출력용 배치 (바닥에 눕힘) ───────────────────────────
if (part == "assembly") assembly();
else if (part == "base") base();
else if (part == "lid") translate([0, 0, lid_top]) rotate([180, 0, 0]) lid();
else if (part == "pin") pin();
else if (part == "lever_a") translate([0, 0, lever_t/2]) rotate([180, 0, 0]) lever(L_a);
else if (part == "lever_b") translate([0, 0, lever_t/2]) rotate([180, 0, 0]) lever(L_b);
else if (part == "servo_mount") translate([0, 0, -mount_z0]) servo_mount();
else if (part == "fit_test") fit_test();
else if (part == "cutaway") difference() { assembly(); translate([-100, -200, -1]) cube([200, 200, 100]); }

echo(str("핀 길이(플랜지 위)=", pin_len, "  레버 L_a=", L_a, "  L_b=", L_b,
         "  뚜껑 윗면 높이=", lid_top, "  상자 바깥 크기=", 2*outer));
