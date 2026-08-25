import math

def SpringStep(current, velocity, target, stiffness, damping, dt):
    omega = math.sqrt(stiffness)
    zeta = damping / (2 * omega)
    y0 = current - target

    if zeta < 1.0:
        wd = omega * math.sqrt(1 - zeta * zeta)
        exp_term = math.exp(-zeta * omega * dt)

        A = y0
        B = (velocity + zeta * omega * y0) / wd

        cos_wd = math.cos(wd * dt)
        sin_wd = math.sin(wd * dt)

        y = exp_term * (A * cos_wd + B * sin_wd)
        v = exp_term * (
            (-zeta * omega) * (A * cos_wd + B * sin_wd) + wd * (-A * sin_wd + B * cos_wd)
        )
    else:
        exp_term = math.exp(-omega * dt)

        A = y0
        B = velocity + omega * y0

        y = exp_term * (A + B * dt)
        v = exp_term * (B - omega * (A + B * dt))

    new_pos = target + y
    new_vel = v
    return new_pos, new_vel
