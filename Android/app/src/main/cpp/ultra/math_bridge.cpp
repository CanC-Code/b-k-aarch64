#include <cmath>
#include <cstring>

extern "C" {

/* Real defs live in src/core1/ml.c after all shadow stubs removed */
extern void ml_vec3f_copy(float* dst, const float* src);
extern void ml_vec3f_clear(float* v);
extern void ml_vec3f_normalize(float* v);
extern void ml_vec3f_set_length(float* v, float len);
extern float ml_vec3f_length(const float* v);
extern int ml_isNonzero_vec3f(const float* v);
extern void ml_vec3f_yaw_rotate_copy(float* dst, const float* src, float yaw);
extern void ml_vec3f_add(float* dst, const float* a, const float* b);
extern void ml_vec3f_scale(float* v, float s);

/* Only defs here that have no src/core1/ml.c counterpart */
void ml_vec3f_set(float* v, float x, float y, float z) {
    v[0] = x;
    v[1] = y;
    v[2] = z;
}

void ml_vec3f_sub(float* out, const float* a, const float* b) {
    out[0] = a[0] - b[0];
    out[1] = a[1] - b[1];
    out[2] = a[2] - b[2];
}

float gu_sqrtf(float x) {
    return sqrtf(x);
}

} // extern "C"
