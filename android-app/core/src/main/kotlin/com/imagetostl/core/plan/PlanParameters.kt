package com.imagetostl.core.plan

/** One numeric dimension of one component, exposed for a UI to display and edit (e.g. as a slider). */
data class PlanParameter(
    val componentIndex: Int,
    val fromCuts: Boolean,
    val field: Field,
    val value: Double,
) {
    enum class Field { SIZE_X, SIZE_Y, SIZE_Z, RADIUS, DEPTH }

    fun label(component: Component): String {
        val axis = when (field) {
            Field.SIZE_X -> "width (x)"
            Field.SIZE_Y -> "depth (y)"
            Field.SIZE_Z -> "height (z)"
            Field.RADIUS -> "radius"
            Field.DEPTH -> "depth"
        }
        return "${component.name} $axis"
    }
}

/** Every numeric dimension of every component/cut in the plan, in a stable order, for driving a slider list. */
fun ComponentPlan.editableParameters(): List<PlanParameter> {
    val params = mutableListOf<PlanParameter>()
    fun collect(components: List<Component>, fromCuts: Boolean) {
        for ((i, c) in components.withIndex()) {
            when (c.type) {
                "box" -> {
                    val s = c.size ?: continue
                    params.add(PlanParameter(i, fromCuts, PlanParameter.Field.SIZE_X, s[0]))
                    params.add(PlanParameter(i, fromCuts, PlanParameter.Field.SIZE_Y, s[1]))
                    params.add(PlanParameter(i, fromCuts, PlanParameter.Field.SIZE_Z, s[2]))
                }
                "cylinder" -> {
                    c.radius?.let { params.add(PlanParameter(i, fromCuts, PlanParameter.Field.RADIUS, it)) }
                    c.depth?.let { params.add(PlanParameter(i, fromCuts, PlanParameter.Field.DEPTH, it)) }
                }
            }
        }
    }
    collect(model.components, fromCuts = false)
    collect(model.cuts, fromCuts = true)
    return params
}

/** Returns a copy of the plan with [param]'s dimension set to [newValue]. */
fun ComponentPlan.withParameterValue(param: PlanParameter, newValue: Double): ComponentPlan {
    fun update(components: List<Component>): List<Component> =
        components.mapIndexed { i, c ->
            if (i != param.componentIndex) c
            else when (param.field) {
                PlanParameter.Field.SIZE_X -> c.copy(size = listOf(newValue, c.size!![1], c.size[2]))
                PlanParameter.Field.SIZE_Y -> c.copy(size = listOf(c.size!![0], newValue, c.size[2]))
                PlanParameter.Field.SIZE_Z -> c.copy(size = listOf(c.size!![0], c.size[1], newValue))
                PlanParameter.Field.RADIUS -> c.copy(radius = newValue)
                PlanParameter.Field.DEPTH -> c.copy(depth = newValue)
            }
        }

    return if (param.fromCuts) {
        copy(model = model.copy(cuts = update(model.cuts)))
    } else {
        copy(model = model.copy(components = update(model.components)))
    }
}
