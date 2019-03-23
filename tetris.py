#!/usr/bin/env python
import os
import sys
import pickle
import random


class BlockMap:
    def link_proto(self, proto):
        self.__squares = proto
        self.width = len(proto[0])
        self.height = len(proto)

    def alloc(self, w, h):
        self.width = w
        self.height = h
        self.__squares = [[False for x in range(0, w)] for y in range(0, h)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width \
           and 0 <= y < self.height

    def get(self, x, y):
        return self.__squares[y][x]

    def set(self, x, y):
        self.__squares[y][x] = True

    def check_row(self, y):
        for block in self.__squares[y]:
            if not block:
                return False
        return True

    def burn_row(self, y):
        for current_index in reversed(range(1, y + 1)):
            self.__squares[current_index] = self.__squares[current_index - 1]
        self.__squares[0] = [False for x in range(0, self.width)]

    def consume(self, map, offset_x, offset_y):
        map.for_each(lambda x, y: self.set(x + offset_x, y + offset_y))

    def for_each(self, f):
        for x in range(0, self.width):
            for y in range(0, self.height):
                if self.get(x, y):
                    f(x, y)


class Shape(BlockMap):
    def __init__(self, sq):
        self.link_proto(sq[0])
        self.full_sq_data = sq
        self.angle = 0
        self.x = 0
        self.y = 0

    def setPos(self, pos):
        self.x = pos[0]
        self.y = pos[1]

    def tryMove(self, field, vec_x, vec_y):
        if self.collision(field, vec_x, vec_y):
            return False
        self.x += vec_x
        self.y += vec_y
        return True

    def tryDrop(self, field):
        pass
        while self.tryMove(field, 0, 1):
            pass
        return True

    def tryRotate(self, field):
        dx = self.width / 2 - 1
        dy = self.height / 2 - 1
        delta = int(dx - dy)    #todo: remove int_cast

        self.angle = self.nextAngleID()
        self.link_proto(self.full_sq_data[self.angle])

        if not self.collision(field, delta, -delta):
            self.x += delta
            self.y -= delta
            return True
        elif not self.collision(field, delta + 1, -delta):
            self.x += delta + 1
            self.y -= delta
            return True
        elif not self.collision(field, delta + 1, -delta + 1):
            self.x += delta + 1
            self.y -= delta - 1
            return True
        elif not self.collision(field, delta, -delta + 1):
            self.x += delta
            self.y -= delta - 1
            return True
        else:
            self.angle = self.prevAngleID()
            self.link_proto(self.full_sq_data[self.angle])
            return False

    def nextAngleID(self):
        if self.angle == 3:
            return 0
        else:
            return self.angle + 1

    def prevAngleID(self):
        if self.angle == 0:
            return 3
        else:
            return self.angle - 1

    def collision(self, field, offset_x=0, offset_y=0):
        if field.blockOutsideBorders(self.x + offset_x,
                                     self.y + offset_y):
            return True
        if field.blockOutsideBorders(self.x + self.width + offset_x - 1,
                                     self.y + self.height + offset_y - 1):
            return True

        for block_x in range(0, self.width):
            for block_y in range(0, self.height):
                if self.get(block_x, block_y):
                    if field.get(self.x + block_x + offset_x
                                ,self.y + block_y + offset_y):
                        return True
        return False


class Field(BlockMap):
    def __init__(self, w=10, h=20):
        self.alloc(w, h)

    def make_copy(self):
        result = Field(self.width, self.height)
        result.consume(self, 0, 0)
        return result

    def blockOutsideBorders(self, pos_x, pos_y):
        x_outside = pos_x < 0 or pos_x >= self.width
        y_outside = pos_y < 0 or pos_y >= self.height
        return x_outside or y_outside

    def defaultRespawnPos(self, shape):
        return int(self.width / 2) - int(shape.width / 2), 0

    def updateRows(self):
        for current_index in reversed(range(0, self.height)):
            while self.check_row(current_index):
                self.burn_row(current_index)


class TetrisCore:

    def __init__(self):
        self.shapePrototypes = self.loadShapePrototypes("prototypes")
        self.field = Field()
        self.shape = self.trySpawnShape(self.randomShape())
        self.nextShape = self.randomShape()
        self.running = True

    def onKey(self, key):
        if key == "left":
            self.shape.tryMove(self.field, -1, 0)
        if key == "right":
            self.shape.tryMove(self.field, 1, 0)
        if key == "down":
            self.shape.tryMove(self.field, 0, 1)
        if key == "land":
            self.shape.tryDrop(self.field)
            self.onShapeLanding()
        if key == "rotate":
            self.shape.tryRotate(self.field)

    def loadShapePrototypes(self, filename):
        return pickle.load(open(filename, "rb"))

    def randomShape(self):
        return Shape(self.shapePrototypes[random.randint(0, len(self.shapePrototypes) - 1)])

    def onShapeLanding(self):
        self.field.consume(self.shape, self.shape.x, self.shape.y)
        self.field.updateRows()
        self.shape = self.trySpawnShape(self.nextShape)
        self.nextShape = self.randomShape()

    def trySpawnShape(self, prototype):
        newshape = prototype
        newshape.setPos(self.field.defaultRespawnPos(newshape))
        if newshape.collision(self.field):
            self.gameOver()
        return newshape

    def tryNextScene(self):
        if not self.running:
            return
        if not self.shape.tryMove(self.field, 0, 1):
            self.onShapeLanding()

    def gameOver(self):
        print("Game Over")
        self.running = False


try:
    print("Trying pyqt5...")
    from PyQt5 import QtCore, QtGui, QtWidgets

except:
    print("Failed!")
    pyqt_ready = False

else:
    print("Done!")
    pyqt_ready = True


try:
    print("Trying glut")
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *

except:
    print("Failed!")
    glut_ready = False

else:
    print("Done!")
    glut_ready = True


try:
    print("Trying pygame...")
    import pygame
    from pygame.locals import *

except:
    print("Failed!")
    pygame_ready = False

else:
    print("Done!")
    pygame_ready = True

print("Select GUI:")
if pyqt_ready:
    print("1. pyqt")
if glut_ready:
    print("2. glut")
if pygame_ready:
    print("3. pygame")

if not (pyqt_ready or glut_ready or pygame_ready):
    print("No GUI installed! Try pyqt5, pygl or pygame.")

if sys.version_info < (3, 0):
    gui = raw_input()
else:
    gui = input()


class AbstractTetrisWidget:

    def __init__(self):
        self.core = TetrisCore()
        self.keys = {}
        self.setSize(300, 300)
        self.abstractTimer(1000, self.onTick)

    def setSize(self, w, h):
        self.width, self.height = w, h

    def onTick(self):
        self.core.tryNextScene()
        self.update()

    def onKey(self, key):
        if not self.core.running:
            return
        translated_key = self.keys.get(key)
        if translated_key:
            self.core.onKey(translated_key)
            self.update()

    def drawBlockMap(self, painter, map, off_x, off_y, draw_frame):
        map.for_each(lambda x, y: painter.drawRect((x + off_x) * 10 + 1, (y + off_y) * 10 + 1, 8, 8))
        if draw_frame:
            painter.drawRect(off_x * 10, off_y * 10, map.width * 10, map.height * 10)

    def onPaint(self, painter):
        painted_field = self.core.field.make_copy()
        painted_field.consume(self.core.shape, self.core.shape.x, self.core.shape.y)
        self.drawBlockMap(painter, painted_field, 0, 0, True)
        self.drawBlockMap(painter, self.core.nextShape, self.core.field.width + 5, 8, False)


if gui == '1' and pyqt_ready:
    print("Switching to pyqt5")


    class QtTetrisWidget(QtWidgets.QWidget, AbstractTetrisWidget):

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent)
            AbstractTetrisWidget.__init__(self)
            self.keys = {QtCore.Qt.Key_Left: "left",
                         QtCore.Qt.Key_Right: "right",
                         QtCore.Qt.Key_Down: "down",
                         QtCore.Qt.Key_End: "land",
                         QtCore.Qt.Key_Space: "rotate"}

        def setSize(self, w, h):
            AbstractTetrisWidget.setSize(self, w, h)
            self.setMinimumSize(w, h)
            self.setMaximumSize(w, h)

        def paintEvent(self, QPaintEvent):
            painter = QtGui.QPainter()
            painter.begin(self)
            self.onPaint(painter)
            painter.end()

        def keyPressEvent(self, event):
            if type(event) == QtGui.QKeyEvent:
                self.onKey(event.key())

        def abstractTimer(self, ms, callback):
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(callback)
            self.timer.start(ms)


    app = QtWidgets.QApplication(sys.argv)

    window = QtTetrisWidget()
    window.show()

    sys.exit(app.exec_())

elif gui == '2' and glut_ready:
    print("Switching to glut")


    class GlutTetrisWidget(AbstractTetrisWidget):

        def __init__(self):
            AbstractTetrisWidget.__init__(self)
            self.keys = {(None, GLUT_KEY_LEFT): "left",
                         (None, GLUT_KEY_RIGHT): "right",
                         (None, GLUT_KEY_DOWN): "down",
                         (None, GLUT_KEY_END): "land",
                         (' ', None): "rotate"}

            glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
            glutInitWindowSize(self.width, self.height)
            glutInit(sys.argv)
            glutCreateWindow(b"Tetris")

            self.onGlutSpecialWrapper = lambda key, x, y: self.onKey((None, key))
            glutSpecialFunc(self.onGlutSpecialWrapper)

            self.onGlutNormalWrapper = lambda key, x, y: self.onKey((key, None))
            glutKeyboardFunc(self.onGlutNormalWrapper)

            self.onGlutDrawWrapper = lambda: self.paintEvent()
            glutDisplayFunc(self.onGlutDrawWrapper)

            self.onGlutTimerWrapper = lambda timerid: self.onGlutTimer()
            glutTimerFunc(self.timer_interval, self.onGlutTimerWrapper, 0)

            self.update()

        def paintEvent(self):
            glClear(GL_COLOR_BUFFER_BIT)
            glPushMatrix()
            glScalef(-.005, .005, .005)
            glRotate(180, 0, 0, 1)
            self.onPaint(self)
            glPopMatrix()
            glutSwapBuffers()

        def drawRect(self, x, y, w, h):
            glBegin(GL_LINE_LOOP)
            glVertex2f(x, y+h)
            glVertex2f(x+w, y+h)
            glVertex2f(x+w, y)
            glVertex2f(x, y)
            glEnd()

        def update(self):
            glutPostRedisplay()

        def abstractTimer(self, ms, callback):
            self.timer_interval = ms
            self.timer_callback = callback

        def onGlutTimer(self):
            glutTimerFunc(self.timer_interval, self.onGlutTimerWrapper, 0)
            self.timer_callback()


    window = GlutTetrisWidget()
    glutMainLoop()


elif gui == '3' and pygame_ready:
    print("Switching to pygame")


    class PygameTetrisWidget(AbstractTetrisWidget):

        def __init__(self):
            AbstractTetrisWidget.__init__(self)
            self.keys = {K_LEFT: "left",
                         K_RIGHT: "right",
                         K_DOWN: "down",
                         K_END: "land",
                         K_SPACE: "rotate"}

            pygame.init()

            self.black = 0, 0, 0
            self.white = 255, 255, 255
            self.screen = pygame.display.set_mode(self.size)
            self.clock = pygame.time.Clock()

            self.update()

        def drawRect(self, x, y, w, h):
            pygame.draw.rect(self.screen, self.white, (x, y, w, h), 1)

        def update(self):
            self.screen.fill(self.black)
            self.onPaint(self)
            pygame.display.update()

        def mainLoop(self):
            while 1:
                self.clock.tick(60)
                for event in pygame.event.get():
                    if event.type == KEYDOWN:
                        self.onKey(event.key)
                        if event.key == K_ESCAPE:
                            return
                    if event.type == pygame.USEREVENT:
                        self.timer_callback()

        def abstractTimer(self, ms, callback):
            pygame.time.set_timer(pygame.USEREVENT, ms)
            self.timer_callback = callback

    window = PygameTetrisWidget()
    window.mainLoop()

else:
    print("Bad input!")
