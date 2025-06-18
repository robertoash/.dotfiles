# Kanata Toggle Key Configuration Examples

## Current Configuration: Hyper+k

Your kanata config is currently set to use **Hyper+k** as the toggle key.

## How to Change the Toggle Key

### Example 1: Change to Hyper+p

To change from Hyper+k to Hyper+p:

1. **In the `unified-hyper` layer** (around line 129):
   ```
   ;; Change this line:
   _    (multi @hyper-mod a)    (multi @hyper-mod s)    (multi @hyper-mod d)    (multi @hyper-mod f)    (multi @hyper-mod g)    (multi @hyper-mod h)    (multi @hyper-mod j)    @kanata-toggle-to-plain    (multi @hyper-mod l)    _    _    _

   ;; To this:
   _    (multi @hyper-mod a)    (multi @hyper-mod s)    (multi @hyper-mod d)    (multi @hyper-mod f)    (multi @hyper-mod g)    (multi @hyper-mod h)    (multi @hyper-mod j)    (multi @hyper-mod k)    (multi @hyper-mod l)    _    _    _

   ;; And change the p position in the line above:
   _    (multi @hyper-mod q)    (multi @hyper-mod w)    (multi @hyper-mod e)    (multi @hyper-mod r)    (multi @hyper-mod t)    (multi @hyper-mod y)    (multi @hyper-mod u)    (multi @hyper-mod i)    (multi @hyper-mod o)    @kanata-toggle-to-plain    _    _    _
   ```

2. **In the `hyper-almost-unchanged` layer** (around line 149):
   ```
   ;; Make the same changes here, but use @kanata-toggle-to-nordic instead
   ```

### Example 2: Change to Hyper+j

To change to Hyper+j, move the toggle aliases to the `j` position in both layers.

### Example 3: Change to Hyper+t

To change to Hyper+t, move the toggle aliases to the `t` position in both layers.

## Key Positions Reference

```
Row 1: q w e r t y u i o p
Row 2: a s d f g h j k l ö ä
Row 3: z x c v b n m
```

Just move `@kanata-toggle-to-plain` and `@kanata-toggle-to-nordic` to your desired key position!