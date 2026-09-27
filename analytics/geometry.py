def point_inside_polygon(point, polygon):
    x, y = point
    inside = False

    j = len(polygon) - 1

    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if ((yi > y) != (yj > y)):
            x_intersection = (xj - xi) * (y - yi) / (yj - yi) + xi

            if x < x_intersection:
                inside = not inside

        j = i

    return inside