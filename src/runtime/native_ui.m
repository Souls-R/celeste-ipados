#import <UIKit/UIKit.h>
#import <GameController/GameController.h>
#import <QuartzCore/QuartzCore.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <stdint.h>
#include <stddef.h>

static NSDictionary *Strings;
static NSDictionary *TextImages;
static BOOL NoticeFinished;

static UIColor *RGB(unsigned color)
{
    return [UIColor colorWithRed:((color >> 16) & 255)/255.0 green:((color >> 8) & 255)/255.0 blue:(color & 255)/255.0 alpha:1];
}
static NSString *Text(NSString *key) { return Strings[key] ?: key; }
static void LoadStrings(void)
{
    NSString *language = NSLocale.preferredLanguages.firstObject.lowercaseString ?: @"en";
    BOOL traditional = ![language containsString:@"hans"] &&
        ([language containsString:@"hant"] || [language containsString:@"-tw"] || [language containsString:@"-hk"] || [language containsString:@"-mo"]);
    NSString *selected = [language hasPrefix:@"zh"] ? (traditional ? @"zh-Hant" : @"zh-Hans") : @"en";
    NSString *path = [NSBundle.mainBundle.bundlePath stringByAppendingPathComponent:@"native-ui/strings.json"];
    NSData *data = [NSData dataWithContentsOfFile:path];
    NSDictionary *all = data ? [NSJSONSerialization JSONObjectWithData:data options:0 error:nil] : nil;
    Strings = all[selected] ?: all[@"en"] ?: @{};
    NSMutableDictionary *images=[NSMutableDictionary dictionary];
    for (NSString *key in Strings) {
        NSString *relative=[NSString stringWithFormat:@"native-ui/rendered/%@/%@.png",selected,key];
        UIImage *image=[UIImage imageWithContentsOfFile:[NSBundle.mainBundle.bundlePath stringByAppendingPathComponent:relative]];
        if (image) images[Strings[key]]=image;
    }
    TextImages=images;
}

int CelesteNativeSettingsFlags(void)
{
    NSUserDefaults *prefs = NSUserDefaults.standardUserDefaults;
    [prefs registerDefaults:@{@"NativeShowNotice":@YES, @"NativeMetalHUD":@NO, @"NativeDiagnosticLogs":@NO}];
    // Environment variables alone can be read before managed Main on iOS.
    // Mirror the switch to Apple's documented defaults key and explicitly set
    // the real SDL/FNA Metal layer after the renderer has been initialized.
    [prefs setBool:[prefs boolForKey:@"NativeMetalHUD"] forKey:@"MetalForceHudEnabled"];
    [prefs setBool:[prefs boolForKey:@"NativeMetalHUD"] forKey:@"MetalHUDForceEnabled"];
    // Same native Metal HUD and configuration as the Silksong port.
    setenv("MTL_HUD_ENABLED", [prefs boolForKey:@"NativeMetalHUD"] ? "1" : "0", 1);
    setenv("MTL_HUD_ALIGNMENT", "bottomright", 1);
    setenv("MTL_HUD_SCALE", "0.20", 1);
    setenv("MTL_HUD_ELEMENTS", "fps,frameinterval,gputime,frameintervalgraph", 1);
    setenv("MTL_HUD_LOGGING_ENABLED", "0", 1);
    return ([prefs boolForKey:@"NativeDiagnosticLogs"] ? 1 : 0)
        | ([prefs boolForKey:@"NativeShowNotice"] ? 2 : 0)
        | ([prefs boolForKey:@"NativeMetalHUD"] ? 4 : 0);
}

static int ApplyMetalHUDToLayer(CALayer *layer, BOOL enabled)
{
    int count=0;
    if (@available(iOS 16.0, *)) {
        if ([layer isKindOfClass:CAMetalLayer.class]) {
            CAMetalLayer *metal=(CAMetalLayer *)layer;
            NSMutableDictionary *properties=[metal.developerHUDProperties mutableCopy] ?: [NSMutableDictionary dictionary];
            if (enabled) properties[@"mode"]=@"default";
            else [properties removeObjectForKey:@"mode"];
            // The panel switch must never turn on periodic HUD log output.
            [properties removeObjectForKey:@"logging"];
            metal.developerHUDProperties=properties;
            fprintf(stdout,"[HUD] layer=%s enabled=%d mode=%s drawable=%.0fx%.0f\n",
                NSStringFromClass(metal.class).UTF8String,enabled,
                [(metal.developerHUDProperties[@"mode"] ?: @"off") UTF8String],
                metal.drawableSize.width,metal.drawableSize.height);
            fflush(stdout);
            count++;
        }
    }
    for (CALayer *child in layer.sublayers) count+=ApplyMetalHUDToLayer(child,enabled);
    return count;
}

int CelesteApplyMetalHUD(void)
{
    BOOL enabled=[NSUserDefaults.standardUserDefaults boolForKey:@"NativeMetalHUD"];
    int count=0;
    // FNA creates its SDL window hidden and shows it after initialization.
    // Configure its Metal layer before that first visible drawable as well.
    for (UIWindow *window in UIApplication.sharedApplication.windows)
        count+=ApplyMetalHUDToLayer(window.layer,enabled);
    for (UIScene *scene in UIApplication.sharedApplication.connectedScenes)
        if ([scene isKindOfClass:UIWindowScene.class])
            for (UIWindow *window in ((UIWindowScene *)scene).windows)
                count+=ApplyMetalHUDToLayer(window.layer,enabled);
    return count;
}

#ifndef CELESTE_UI_TEST
// SDL2's public SysWM ABI has a 64-byte union, aligned after version/subsystem.
// Obtain the actual UIWindow owned by this SDL window instead of depending on
// UIApplication's legacy global list, which is empty for this renderer on iPad.
typedef struct { uint8_t major,minor,patch; } CelesteSDLVersion;
typedef struct {
    CelesteSDLVersion version;
    int subsystem;
    union { void *window; uint8_t reserved[64]; } info;
} CelesteSDLWMInfo;
_Static_assert(offsetof(CelesteSDLWMInfo,info)==8,"SDL2 SysWM union alignment");
extern void SDL_GetVersion(CelesteSDLVersion *version);
extern int SDL_GetWindowWMInfo(void *window, CelesteSDLWMInfo *info);
#endif

int CelesteApplyMetalHUDToWindow(void *sdlWindow)
{
#ifndef CELESTE_UI_TEST
    CelesteSDLWMInfo info={0}; SDL_GetVersion(&info.version);
    int ok=SDL_GetWindowWMInfo(sdlWindow,&info);
    fprintf(stdout,"[HUD] SDL window=%p WM subsystem=%d ok=%d nativeWindow=%p\n",sdlWindow,info.subsystem,ok,info.info.window);
    if (ok && info.subsystem==5 && info.info.window) {
        UIWindow *window=(__bridge UIWindow *)info.info.window;
        BOOL enabled=[NSUserDefaults.standardUserDefaults boolForKey:@"NativeMetalHUD"];
        // SDL may have assigned its controller view before UIKit attaches its
        // backing layer to the window. Query that controller view directly.
        UIView *view=window.rootViewController.view;
        int count=ApplyMetalHUDToLayer(view.layer,enabled);
        if (!count) count=ApplyMetalHUDToLayer(window.layer,enabled);
        fprintf(stdout,"[HUD] SDL root=%s configured=%d\n",NSStringFromClass(view.class).UTF8String,count);
        fflush(stdout);
        if (count) return count;
    }
#endif
    return CelesteApplyMetalHUD();
}

void CelesteConfigureNativeLogging(const char *path)
{
    BOOL enabled = [NSUserDefaults.standardUserDefaults boolForKey:@"NativeDiagnosticLogs"];
    // This controls SDL/native stdout as well as the managed runtime.log switch.
    // Normal logs do no file I/O when disabled. iOS crash reports remain available.
    fflush(stdout); fflush(stderr);
    if (enabled) { FILE *reset=fopen(path,"w"); if (reset) fclose(reset); }
    freopen(enabled ? path : "/dev/null", "a", stdout);
    freopen(enabled ? path : "/dev/null", "a", stderr);
    if (enabled) { setvbuf(stdout, NULL, _IOLBF, 0); setvbuf(stderr, NULL, _IOLBF, 0); }
}

@interface CelesteSkyView : UIView
@end
@implementation CelesteSkyView
- (void)drawRect:(CGRect)rect
{
    CGContextRef c=UIGraphicsGetCurrentContext();
    CGColorSpaceRef space=CGColorSpaceCreateDeviceRGB();
    NSArray *colors=@[(id)RGB(0x10182f).CGColor,(id)RGB(0x20203d).CGColor,(id)RGB(0x34304e).CGColor];
    CGFloat stops[]={0,.6,1};
    CGGradientRef gradient=CGGradientCreateWithColors(space,(__bridge CFArrayRef)colors,stops);
    CGContextDrawLinearGradient(c,gradient,CGPointZero,CGPointMake(self.bounds.size.width,self.bounds.size.height),0);
    CGGradientRelease(gradient); CGColorSpaceRelease(space);
    for (int i=0;i<72;i++) {
        CGFloat x=((i*173+37)%1194)/1194.0*self.bounds.size.width;
        CGFloat y=((i*97+23)%834)/834.0*self.bounds.size.height;
        CGContextSetFillColorWithColor(c,[RGB(0xa5bfd6) colorWithAlphaComponent:.12+(i%4)*.04].CGColor);
        CGContextFillEllipseInRect(c,CGRectMake(x,y,1.2,1.2));
    }
}
@end

// Render the same Renogare and Noto bitmap glyphs used by the game. Each label
// is prepared at 3x resolution from the user's font atlas, including matching
// Noto fallback glyphs where the game's subset lacks new notice characters.
@interface CelesteBitmapLabel : UILabel
@end
@implementation CelesteBitmapLabel
- (void)drawRect:(CGRect)rect
{
    UIImage *image=TextImages[self.text];
    if (!image) { [super drawRect:rect]; return; }
    CGSize size=CGSizeMake(image.size.width/3.0,image.size.height/3.0);
    CGFloat scale=MIN(1,MIN(self.bounds.size.width/size.width,self.bounds.size.height/size.height));
    size=CGSizeMake(size.width*scale,size.height*scale);
    CGFloat x=self.textAlignment==NSTextAlignmentRight ? self.bounds.size.width-size.width :
        (self.textAlignment==NSTextAlignmentCenter ? (self.bounds.size.width-size.width)/2 : 0);
    UIImage *colored=[image imageWithTintColor:self.textColor renderingMode:UIImageRenderingModeAlwaysOriginal];
    [colored drawInRect:CGRectMake(x,(self.bounds.size.height-size.height)/2,size.width,size.height)];
}
@end

@interface CelesteNoticeView : UIView
@property(nonatomic,strong) UIView *canvas;
@property(nonatomic,strong) UIButton *enterButton;
@property(nonatomic,strong) UIButton *nextLaunchButton;
@property(nonatomic,strong) UILabel *nextValue;
@property(nonatomic,strong) UIImageView *cursor;
@property(nonatomic,strong) CADisplayLink *controllerPoll;
@property(nonatomic) NSInteger selection;
@property(nonatomic) unsigned previousButtons;
- (void)start;
- (void)stop;
@end

@implementation CelesteNoticeView
- (instancetype)initWithFrame:(CGRect)frame
{
    if ((self=[super initWithFrame:frame])) {
        self.backgroundColor=RGB(0x101933);
        self.accessibilityViewIsModal=YES;
        self.autoresizingMask=UIViewAutoresizingFlexibleWidth|UIViewAutoresizingFlexibleHeight;
        self.canvas=[[UIView alloc] initWithFrame:CGRectMake(0,0,1194,834)];
        [self addSubview:self.canvas];
        CelesteSkyView *sky=[[CelesteSkyView alloc] initWithFrame:self.canvas.bounds];
        sky.opaque=YES; sky.userInteractionEnabled=NO; [self.canvas addSubview:sky];
        NSString *assetRoot=[NSBundle.mainBundle.bundlePath stringByAppendingPathComponent:@"native-ui/rendered"];
        UIImageView *logo=[[UIImageView alloc] initWithImage:[UIImage imageWithContentsOfFile:[assetRoot stringByAppendingPathComponent:@"logo.png"]]];
        logo.frame=CGRectMake(70,230,440,355); logo.contentMode=UIViewContentModeScaleAspectFit;
        [self.canvas addSubview:logo];
        UILabel *subtitle=[self label:Text(@"subtitle") frame:CGRectMake(70,617,440,34) size:13 color:RGB(0x94a9c6)];
        subtitle.textAlignment=NSTextAlignmentCenter;
        [self label:Text(@"noticeTitle") frame:CGRectMake(634,180,440,48) size:30 color:UIColor.whiteColor];
        [self label:Text(@"noticeFree") frame:CGRectMake(634,266,440,82) size:20 color:UIColor.whiteColor];
        [self label:Text(@"noticeResale") frame:CGRectMake(634,365,440,108) size:18 color:RGB(0xc7c7dc)];
        self.enterButton=[self button:Text(@"enterGame") frame:CGRectMake(630,510,440,58) action:@selector(enter:)];
        self.nextLaunchButton=[self button:@"" frame:CGRectMake(630,585,440,48) action:@selector(toggle:)];
        UILabel *next=[[CelesteBitmapLabel alloc] initWithFrame:CGRectMake(4,0,190,48)];
        next.text=Text(@"nextLaunch"); next.textColor=RGB(0xb0afc8); next.font=[UIFont systemFontOfSize:14];
        [self.nextLaunchButton addSubview:next];
        self.nextValue=[[CelesteBitmapLabel alloc] initWithFrame:CGRectMake(205,0,225,48)];
        self.nextValue.font=[UIFont systemFontOfSize:17];
        self.nextValue.textAlignment=NSTextAlignmentRight; self.nextValue.textColor=RGB(0xd4d8ed);
        [self.nextLaunchButton addSubview:self.nextValue];
        [self label:Text(@"noticeHelp") frame:CGRectMake(634,676,440,62) size:13 color:RGB(0x9ba4c1)];
        [self label:Text(@"controls") frame:CGRectMake(634,754,440,30) size:11 color:RGB(0x818aa8)];
        UIImage *arrow=[UIImage imageWithContentsOfFile:[assetRoot stringByAppendingPathComponent:@"dotarrow.png"]];
        self.cursor=[[UIImageView alloc] initWithImage:[arrow imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate]];
        self.cursor.tintColor=RGB(0xfcff59); self.cursor.contentMode=UIViewContentModeScaleAspectFit;
        [self.canvas addSubview:self.cursor];
        self.cursor.isAccessibilityElement=NO;
        [self syncChoice]; [self selectItem:0];
    }
    return self;
}
- (UILabel *)label:(NSString *)text frame:(CGRect)frame size:(CGFloat)size color:(UIColor *)color
{
    UILabel *label=[[CelesteBitmapLabel alloc] initWithFrame:frame];
    label.text=text; label.font=[UIFont systemFontOfSize:size weight:UIFontWeightMedium];
    label.textColor=color; label.textAlignment=NSTextAlignmentLeft; label.numberOfLines=0;
    [self.canvas addSubview:label]; return label;
}
- (UIButton *)button:(NSString *)text frame:(CGRect)frame action:(SEL)action
{
    UIButton *button=[UIButton buttonWithType:UIButtonTypeCustom]; button.frame=frame;
    UIImage *image=TextImages[text];
    if (image) {
        UIImage *sized=[UIImage imageWithCGImage:image.CGImage scale:3 orientation:UIImageOrientationUp];
        [button setImage:[sized imageWithRenderingMode:UIImageRenderingModeAlwaysTemplate] forState:UIControlStateNormal];
    } else [button setTitle:text forState:UIControlStateNormal];
    button.accessibilityLabel=text; button.contentHorizontalAlignment=UIControlContentHorizontalAlignmentLeft;
    button.contentEdgeInsets=UIEdgeInsetsMake(0,4,0,0);
    [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    button.titleLabel.font=[UIFont systemFontOfSize:22 weight:UIFontWeightSemibold];
    button.layer.cornerRadius=2;
    [button addTarget:self action:action forControlEvents:UIControlEventTouchUpInside];
    [self.canvas addSubview:button]; return button;
}
- (void)layoutSubviews
{
    [super layoutSubviews];
    CGRect safe=UIEdgeInsetsInsetRect(self.bounds,self.safeAreaInsets);
    CGFloat scale=MIN(safe.size.width/1194.0,safe.size.height/834.0);
    self.canvas.transform=CGAffineTransformIdentity;
    self.canvas.bounds=CGRectMake(0,0,1194,834);
    self.canvas.center=CGPointMake(CGRectGetMidX(safe),CGRectGetMidY(safe));
    self.canvas.transform=CGAffineTransformMakeScale(scale,scale);
}
- (void)syncChoice
{
    BOOL show=[NSUserDefaults.standardUserDefaults boolForKey:@"NativeShowNotice"];
    self.nextValue.text=Text(show ? @"showNotice" : @"skipNotice");
    self.nextLaunchButton.accessibilityLabel=Text(@"nextLaunch");
    self.nextLaunchButton.accessibilityValue=self.nextValue.text;
}
- (void)selectItem:(NSInteger)selection
{
    self.selection=(selection+2)%2;
    self.enterButton.tintColor=self.selection==0 ? RGB(0xfcff59) : UIColor.whiteColor;
    self.nextValue.textColor=self.selection==1 ? RGB(0xfcff59) : RGB(0xd4d8ed);
    UIButton *selected=self.selection==0 ? self.enterButton : self.nextLaunchButton;
    self.cursor.frame=CGRectMake(selected.frame.origin.x-30,CGRectGetMidY(selected.frame)-12,18,24);
}
- (void)toggle:(id)sender
{
    NSUserDefaults *prefs=NSUserDefaults.standardUserDefaults;
    [prefs setBool:![prefs boolForKey:@"NativeShowNotice"] forKey:@"NativeShowNotice"];
    [self syncChoice];
}
- (void)enter:(id)sender { NoticeFinished=YES; }
- (BOOL)canBecomeFirstResponder { return YES; }
- (NSSet<UIPress *> *)physicalKeyPresses:(NSSet<UIPress *> *)presses
{
    NSMutableSet *keys=[NSMutableSet set];
    for (UIPress *press in presses) if (press.key!=nil) [keys addObject:press];
    return keys;
}
- (void)pressesBegan:(NSSet<UIPress *> *)presses withEvent:(UIPressesEvent *)event
{
    NSSet *keys=[self physicalKeyPresses:presses];
    if (keys.count) [super pressesBegan:keys withEvent:event];
}
- (void)pressesEnded:(NSSet<UIPress *> *)presses withEvent:(UIPressesEvent *)event
{
    NSSet *keys=[self physicalKeyPresses:presses];
    if (keys.count) [super pressesEnded:keys withEvent:event];
}
- (void)pressesCancelled:(NSSet<UIPress *> *)presses withEvent:(UIPressesEvent *)event
{
    NSSet *keys=[self physicalKeyPresses:presses];
    if (keys.count) [super pressesCancelled:keys withEvent:event];
}
- (NSArray<UIKeyCommand *> *)keyCommands
{
    NSMutableArray *result=[NSMutableArray array];
    for (NSString *input in @[UIKeyInputUpArrow,UIKeyInputDownArrow,UIKeyInputLeftArrow,UIKeyInputRightArrow,@"\r",@" "]) {
        UIKeyCommand *key=[UIKeyCommand keyCommandWithInput:input modifierFlags:0 action:@selector(key:)];
        key.wantsPriorityOverSystemBehavior=YES; [result addObject:key];
    }
    return result;
}
- (void)key:(UIKeyCommand *)key
{
    if ([key.input isEqual:UIKeyInputUpArrow] || [key.input isEqual:UIKeyInputDownArrow]) [self selectItem:1-self.selection];
    else if ([key.input isEqual:UIKeyInputLeftArrow] || [key.input isEqual:UIKeyInputRightArrow]) {
        if (self.selection==1) [self toggle:nil];
    } else [(self.selection==0 ? self.enterButton : self.nextLaunchButton) sendActionsForControlEvents:UIControlEventTouchUpInside];
}
- (unsigned)controllerButtons
{
    unsigned result=0;
    for (GCController *controller in GCController.controllers) {
        GCExtendedGamepad *pad=controller.extendedGamepad; if (!pad) continue;
        if (pad.dpad.up.isPressed || pad.dpad.down.isPressed || fabsf(pad.leftThumbstick.yAxis.value)>.6) result|=1;
        if (pad.dpad.left.isPressed || pad.dpad.right.isPressed || fabsf(pad.leftThumbstick.xAxis.value)>.6) result|=2;
        if (pad.buttonA.isPressed || pad.buttonMenu.isPressed) result|=4;
    }
    return result;
}
- (void)handleControllerButtons:(unsigned)current
{
    unsigned pressed=current & ~self.previousButtons; self.previousButtons=current;
    if (pressed&1) [self selectItem:1-self.selection];
    if ((pressed&2) && self.selection==1) [self toggle:nil];
    if (pressed&4) [(self.selection==0 ? self.enterButton : self.nextLaunchButton) sendActionsForControlEvents:UIControlEventTouchUpInside];
}
- (void)pollController:(CADisplayLink *)link { [self handleControllerButtons:[self controllerButtons]]; }
- (void)start
{
    self.previousButtons=[self controllerButtons];
    self.controllerPoll=[CADisplayLink displayLinkWithTarget:self selector:@selector(pollController:)];
    self.controllerPoll.preferredFrameRateRange=CAFrameRateRangeMake(30,60,60);
    [self.controllerPoll addToRunLoop:NSRunLoop.mainRunLoop forMode:NSRunLoopCommonModes];
    [self becomeFirstResponder];
    UIAccessibilityPostNotification(UIAccessibilityScreenChangedNotification,self.enterButton);
}
- (void)stop
{
    [self.controllerPoll invalidate]; self.controllerPoll=nil; [self resignFirstResponder];
}
@end

@interface CelesteNoticeController : UIViewController
@end
@implementation CelesteNoticeController
- (BOOL)prefersStatusBarHidden { return YES; }
- (UIInterfaceOrientationMask)supportedInterfaceOrientations { return UIInterfaceOrientationMaskLandscape; }
- (void)loadView { self.view=[[CelesteNoticeView alloc] initWithFrame:UIScreen.mainScreen.bounds]; }
@end

void CelesteShowLaunchNotice(void)
{
    if (![NSUserDefaults.standardUserDefaults boolForKey:@"NativeShowNotice"]) return;
    LoadStrings(); NoticeFinished=NO;
    UIWindow *previous=nil;
    for (UIWindow *window in UIApplication.sharedApplication.windows) if (window.isKeyWindow) previous=window;
    UIWindowScene *scene=nil;
    for (UIScene *candidate in UIApplication.sharedApplication.connectedScenes) {
        if ([candidate isKindOfClass:UIWindowScene.class] && candidate.activationState!=UISceneActivationStateUnattached) {
            scene=(UIWindowScene *)candidate; break;
        }
    }
    UIWindow *window=scene ? [[UIWindow alloc] initWithWindowScene:scene] : [[UIWindow alloc] initWithFrame:UIScreen.mainScreen.bounds];
    CelesteNoticeController *controller=[CelesteNoticeController new];
    window.rootViewController=controller;
    window.windowLevel=UIWindowLevelNormal+1;
    [window makeKeyAndVisible];
    CelesteNoticeView *view=(CelesteNoticeView *)controller.view;
    [view start];
    // SDL invokes its entry point after UIKit finishes launching. Keep UIKit's
    // run loop alive for this one screen, then hand control to SDL/FNA once.
    while (!NoticeFinished) {
        @autoreleasepool {
            [NSRunLoop.mainRunLoop runMode:NSDefaultRunLoopMode beforeDate:[NSDate dateWithTimeIntervalSinceNow:1.0/60.0]];
        }
    }
    [view stop]; window.hidden=YES; window.rootViewController=nil;
    if (previous) [previous makeKeyWindow];
    TextImages=nil; Strings=nil;
    // No notice window, controller poll or extra rendering loop survives handoff.
}
