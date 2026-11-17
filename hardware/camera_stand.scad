// 카메라 스탠드 — Camera Module 3를 문서 위 약 30cm에 아래로 향하게 고정
// 라즈베리파이 4를 같은 팔 위, 카메라 가까이에 올려 기본 카메라 케이블로 연결한다.
//
// 부품 (괄호 = 출력 개수): stand_base(1)  column(seg_count)  arm(1)
// 나사 없음: 기둥은 사각 돌기로 끼우고, 보드는 출력된 핀에 끼운다 (헐거우면 순간접착제 한 방울)

part = "assembly";

/* [기둥] */
col        = 20;    // 기둥 단면 (정사각형)
seg_len    = 100;   // 기둥 한 토막 길이 (프린터 높이에 맞게)
seg_count  = 3;     // 토막 개수 → 카메라 높이 약 seg_len × seg_count
peg        = 10;    // 연결 돌기 크기
peg_h      = 10;
clr        = 0.4;   // 끼움 여유 (fit_test 결과를 참고해 조정)

/* [받침] */
base_w     = 160;
base_d     = 120;
base_t     = 5;

/* [팔] */
arm_len    = 140;   // 기둥 중심 ~ 카메라 중심
arm_w      = 66;
arm_t      = 5;
rib_h      = 8;
rib_t      = 2.5;

/* [보드 치수] */
cam_holes  = [21, 12.5];    // Camera Module 3 장착 구멍 간격 (M2)
cam_peg_d  = 1.9;
pi_holes   = [58, 49];      // Raspberry Pi 4 장착 구멍 간격 (M2.5)
pi_peg_d   = 2.3;
pi_center  = 70;            // 기둥 중심 ~ 파이 중심 (카메라 케이블이 닿도록 카메라 가까이)
standoff_h = 4;

$fn = 32;

// ── 받침 ──────────────────────────────────────────────
module stand_base() {
    // 받침은 기둥 뒤(+y)로 뻗고, 기둥 앞(-y)은 문서 자리로 비워 둔다.
    // 무게중심이 기둥 조금 앞에 있으므로 받침 위에 책 등을 올려 두면 더 안정적이다
    difference() {
        union() {
            translate([-base_w/2, -col/2 - 6, 0]) cube([base_w, base_d, base_t]);
            translate([-col/2 - 6, -col/2 - 6, 0]) cube([col + 12, col + 12, base_t + 20]);
        }
        translate([-(col + clr)/2, -(col + clr)/2, base_t + 2]) cube([col + clr, col + clr, 30]);
    }
}

// ── 기둥 한 토막: 위에 돌기, 아래에 구멍 ─────────────────
module column() {
    difference() {
        translate([-col/2, -col/2, 0]) cube([col, col, seg_len]);
        translate([-(peg + clr)/2, -(peg + clr)/2, -1]) cube([peg + clr, peg + clr, peg_h + 1.5]);
    }
    translate([-peg/2, -peg/2, seg_len]) cube([peg, peg, peg_h]);
}

module peg_standoff(d) {
    cylinder(d = d + 2.5, h = standoff_h);
    cylinder(d = d, h = standoff_h + 2.5);
}

// ── 팔: 기둥 위 돌기에 끼움. 파이는 위, 카메라는 렌즈가 구멍으로 아래를 보게 엎어서 ──
module arm() {
    difference() {
        union() {
            translate([-arm_w/2, -arm_len - 20, 0]) cube([arm_w, arm_len + 35, arm_t]);
            // 양옆 보강 리브
            for (x = [-arm_w/2, arm_w/2 - rib_t])
                translate([x, -arm_len + 10, 0]) cube([rib_t, arm_len + 5, rib_h]);
            // 기둥 연결부
            translate([-col/2 - 4, -col/2 - 4, 0]) cube([col + 8, col + 8, peg_h]);
        }
        // 기둥 돌기 구멍
        translate([-(peg + clr)/2, -(peg + clr)/2, -1]) cube([peg + clr, peg + clr, peg_h + 2]);
        // 렌즈 구멍 (카메라를 엎어 놓으면 렌즈가 이 구멍으로 아래를 본다)
        translate([-7.5, -arm_len - 14, -1]) cube([15, 28, arm_t + 2]);
    }
    // 카메라 핀 (보드를 엎어서 끼움)
    for (dx = [-cam_holes[0]/2, cam_holes[0]/2], dy = [-cam_holes[1]/2, cam_holes[1]/2])
        translate([dx, -arm_len + dy, arm_t]) peg_standoff(cam_peg_d);
    // 라즈베리파이 핀 (구멍 간격 58 = 팔 길이 방향, 49 = 폭 방향)
    for (dy = [-pi_holes[0]/2, pi_holes[0]/2], dx = [-pi_holes[1]/2, pi_holes[1]/2])
        translate([dx, -pi_center + dy, arm_t]) peg_standoff(pi_peg_d);
}

module assembly() {
    color("lightgray") stand_base();
    for (k = [0:seg_count - 1])
        translate([0, 0, base_t + 2 + k * seg_len]) color(k % 2 ? "silver" : "gainsboro") column();
    translate([0, 0, base_t + 2 + seg_count * seg_len]) {
        color("tomato") arm();
        // 파이 보드 (미리보기)
        color("green", 0.6) translate([-28, -pi_center - 42.5, arm_t + standoff_h]) cube([56, 85, 1.5]);
        // 카메라 보드 (미리보기, 엎어 놓음)
        color("darkgreen") translate([-12.5, -arm_len - 12, arm_t + standoff_h]) cube([25, 24, 1]);
    }
    // 문서 자리 (A4, 미리보기)
    color("white", 0.5) translate([-148.5, -arm_len - 105, 0]) cube([297, 210, 0.2]);
}

if (part == "assembly") assembly();
else if (part == "stand_base") stand_base();
else if (part == "column") column();
else if (part == "arm") arm();

echo(str("렌즈 높이(바닥 기준) 약 ", base_t + 2 + seg_count * seg_len, "mm, 카메라 중심은 기둥에서 ", arm_len, "mm 앞"));
