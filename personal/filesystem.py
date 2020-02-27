from .models import Profile, ImageFile
import os

def handle_image_upload(f, fname, iid, tags):
    #don't try to say if not exists, throws error for a reason I don't understand
    ext = fname.split('.')[1]
    if(os.path.exists('personal/static/personal/images/'+iid+'.'+ext)):
        return handle_image_upload(f, iid+'a', tags)
    else:
        image = ImageFile(image_ID=iid,tags=tags,ext=ext)
        image.save()
        with open('personal/static/personal/images/'+iid+'.'+ext, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        return ''+iid+'.'+ext
    
def handle_create_new_user(f, pid, pword, bio, dname):
    user = Profile(profile_ID=pid, resume=pid, pword=pword, bio=bio, display_Name=dname)
    user.save()
    with open('personal/static/personal/resumes/'+pid+'.pdf', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return pid